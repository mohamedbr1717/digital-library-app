# app/main.py
import uuid
from fastapi import FastAPI, Request, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from beanie import init_beanie, PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import logging
from datetime import timedelta

# --- استيراد من ملفات المشروع المنظمة ---
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, get_current_admin_user
from app.db.models import User, BaseContent, Feedback, UserIn, Token, FeedbackIn, ContentCreateIn, ContentUpdateIn
from app.db.error_models import LibraryException, APIErrorResponse, ErrorLog, ContentNotFoundError, ValidationError, AuthenticationError
from app.services.content_service import ContentService # ✅ استيراد خدمة المحتوى
from app.services.user_service import UserService # ✅ استيراد خدمة المستخدم
from app.db.static_data import EDUCATIONAL_BOOKS_DATA # ✅ استيراد البيانات الثابتة للكتب

# --- تهيئة تطبيق FastAPI ---
app = FastAPI(
    title="المكتبة الرقمية",
    description="واجهة برمجية لمشروع المكتبة الرقمية الشاملة",
    version="1.0.0"
)

# --- إعداد CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- إعداد قوالب HTML والملفات الثابتة ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# --- دوال بدء التشغيل والإيقاف ---
@app.on_event("startup")
async def startup_event():
    client = AsyncIOMotorClient(settings.DB_URI)
    await init_beanie(
        database=client[settings.DB_NAME],
        document_models=[User, BaseContent, Feedback, ErrorLog]
    )
    print("Successfully connected to the database.")

# --- Middleware ومعالجات الأخطاء ---
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.exception_handler(LibraryException)
async def handle_library_exceptions(request: Request, exc: LibraryException):
    error_log = ErrorLog(
        error_type=exc.error_type,
        message=exc.message,
        details=[d.dict() for d in exc.details],
        request_id=getattr(request.state, 'request_id', None),
        endpoint=str(request.url),
        method=request.method,
        user_id=getattr(request.state, 'user_id', None) if hasattr(request.state, 'user_id') else None
    )
    await error_log.insert()
    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorResponse(
            type=exc.error_type,
            message=exc.message,
            details=[d.dict() for d in exc.details],
            request_id=request.state.request_id
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def handle_validation_errors(request: Request, exc: RequestValidationError):
    details = []
    for error in exc.errors():
        details.append({
            "field": ".".join(str(loc) for loc in error['loc']),
            "message": error['msg'],
            "value": error.get('input')
        })
    error_log = ErrorLog(
        error_type="validation_error",
        message="Validation failed",
        details=details,
        request_id=getattr(request.state, 'request_id', None),
        endpoint=str(request.url),
        method=request.method
    )
    await error_log.insert()
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=APIErrorResponse(
            type="validation_error",
            message="Validation failed",
            details=details,
            request_id=request.state.request_id
        ).dict()
    )

# --- نقاط النهاية (API Endpoints) ---

# 1. الواجهات الأمامية (HTML)
@app.get("/", tags=["Frontend"])
def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", tags=["Frontend"])
def serve_admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/books/{book_name}", tags=["Frontend"])
def serve_educational_book(request: Request, book_name: str):
    book_data = EDUCATIONAL_BOOKS_DATA.get(book_name)
    if not book_data:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return templates.TemplateResponse("educational_book_template.html", {"request": request, "book": book_data})

# 2. التوثيق والمستخدمون
@app.post("/api/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.authenticate(form_data.username, form_data.password)
    if not user:
        raise AuthenticationError("بيانات الدخول غير صحيحة")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={"username": user.username, "is_admin": user.is_admin}
    )

@app.post("/api/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register_user(user_in: UserIn):
    # ✅ استخدام خدمة المستخدم
    user = await UserService.create_user(user_in)
    return {"message": "تم إنشاء الحساب بنجاح!"}

# 3. واجهات المحتوى
@app.get("/api/content", response_model=List[BaseContent], tags=["Content"])
async def get_content(
    content_type: str,
    page: int = 1,
    page_size: int = 12,
    q: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    subject: Optional[str] = None
):
    tags = []
    if category and category != "ALL": tags.append(category)
    if level and level != "ALL": tags.append(level)
    if subject and subject != "ALL": tags.append(subject)

    # ✅ استخدام خدمة المحتوى
    content_list = await ContentService.get_content_by_type(content_type, page, page_size, q, tags)
    return content_list

@app.get("/api/content/{item_id}", response_model=BaseContent, tags=["Content"])
async def get_content_item(item_id: PydanticObjectId):
    # ✅ استخدام خدمة المحتوى
    content = await ContentService.get_content_by_id(item_id)
    return content

@app.post("/api/summarize/{item_id}", tags=["Content"])
async def summarize_content(item_id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    from app.services.gemini_utils import generate_gemini_summary

    content = await ContentService.get_content_by_id(item_id)
    
    if content.content_type not in ["book", "educational"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يمكن تلخيص هذا النوع من المحتوى."
        )

    text_to_summarize = content.description or content.title

    if not text_to_summarize:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "لا يوجد نص متاح للتلخيص لهذا المحتوى."}
        )

    summary = generate_gemini_summary(text_to_summarize)
    if summary.startswith("ERROR"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"فشل في توليد الملخص: {summary}"}
        )
    return {"summary": summary}

@app.post("/api/feedback", status_code=status.HTTP_201_CREATED, tags=["Feedback"])
async def post_feedback(feedback_in: FeedbackIn, current_user: User = Depends(get_current_user)):
    content = await ContentService.get_content_by_id(feedback_in.content_id)
    
    feedback = Feedback(
        content_id=feedback_in.content_id,
        user_id=current_user.id,
        username=current_user.username,
        rating=feedback_in.rating,
        comment=feedback_in.comment
    )
    await feedback.insert()

    # ✅ استخدام دالة الخدمة لتحديث التقييم بكفاءة
    await ContentService.update_feedback_and_rating(feedback)

    return {"message": "تم إرسال التقييم بنجاح."}

@app.get("/api/feedback/{content_id}", response_model=List[Feedback], tags=["Feedback"])
async def get_feedback_for_content(content_id: PydanticObjectId):
    # ✅ استخدام خدمة المحتوى
    feedbacks = await ContentService.get_feedback_for_content(content_id)
    return feedbacks

@app.get("/api/admin/stats", tags=["Admin"])
async def get_admin_stats(current_user: User = Depends(get_current_admin_user)):
    # ✅ استخدام خدمة المستخدم
    stats = await UserService.get_admin_stats()
    return stats

# ✅ نقطة نهاية إدارة المحتوى (للمستخدمين الإداريين فقط)
@app.post("/api/content", status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
async def create_content(content_data: ContentCreateIn, current_user: User = Depends(get_current_admin_user)):
    # ✅ استخدام خدمة المحتوى
    content = await ContentService.create_new_content(content_data)
    return content

@app.put("/api/content/{content_id}", tags=["Admin Content"])
async def update_content(content_id: PydanticObjectId, content_data: ContentUpdateIn, current_user: User = Depends(get_current_admin_user)):
    # ✅ استخدام خدمة المحتوى
    content = await ContentService.update_existing_content(content_id, content_data)
    return content

@app.delete("/api/content/{content_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
async def delete_content(content_id: PydanticObjectId, current_user: User = Depends(get_current_admin_user)):
    # ✅ استخدام خدمة المحتوى
    await ContentService.delete_content_by_id(content_id)
    return
