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
from typing import Optional, List, Dict, Any # ✅ تم إضافة Dict, Any
import logging
from datetime import timedelta

# --- استيراد من ملفات المشروع المنظمة ---
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, get_current_admin_user, get_password_hash
from app.db.models import User, BaseContent, Feedback, UserIn, Token, FeedbackIn, ContentCreateIn, ContentUpdateIn # ✅ تم استيراد النماذج الجديدة
from app.db.error_models import LibraryException, APIErrorResponse, ErrorLog, ContentNotFoundError, ValidationError, AuthenticationError

# --- تهيئة تطبيق FastAPI ---
app = FastAPI(
    title="المكتبة الرقمية",
    description="واجهة برمجية لمشروع المكتبة الرقمية الشاملة",
    version="1.0.0"
)

# --- إعداد CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # ✅ ضع قائمة النطاقات المسموحة في الإنتاج
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

# ✅ تم التعديل: نقطة نهاية واحدة للكتب التعليمية الديناميكية
@app.get("/books/{book_name}", tags=["Frontend"])
def serve_educational_book(request: Request, book_name: str):
    """
    يقوم بتقديم صفحة كتاب تعليمي ديناميكيًا باستخدام قالب Jinja2.
    """
    # بيانات الكتب التعليمية
    books_data: Dict[str, Dict[str, Any]] = {
        "arabic_primary": {
            "title": "📘 كتاب اللغة العربية - ابتدائي",
            "description": "أساسيات اللغة العربية للمرحلة الابتدائية.",
            "theme_class": "arabic-primary-theme",
            "sections": [
                {
                    "title": "الوحدة 1: الحروف والكلمات",
                    "items": [
                        {"icon": "📝", "text": "تمرين: كتابة الحروف الأبجدية", "link": "#"},
                        {"icon": "📝", "text": "تمرين: تكوين كلمات بسيطة", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: تعلُّم الحروف بالصوت والصورة", "link": "#"},
                    ]
                },
                {
                    "title": "الوحدة 2: القراءة والفهم",
                    "items": [
                        {"icon": "📝", "text": "تمرين: قراءة نصوص قصيرة", "link": "#"},
                        {"icon": "📝", "text": "تمرين: أسئلة فهم واستيعاب", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: قراءة قصص قصيرة", "link": "#"},
                    ]
                }
            ]
        },
        "physics_middle": {
            "title": "📗 كتاب الفيزياء - إعدادي",
            "description": "مبادئ الفيزياء للمرحلة الإعدادية.",
            "theme_class": "physics-middle-theme",
            "sections": [
                {
                    "title": "الوحدة 1: الحركة والقوى",
                    "items": [
                        {"icon": "📝", "text": "تمرين: قوانين نيوتن", "link": "#"},
                        {"icon": "📝", "text": "تمرين: التسارع والمسافة", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: تطبيقات على الحركة", "link": "#"},
                    ]
                },
                {
                    "title": "الوحدة 2: الطاقة",
                    "items": [
                        {"icon": "📝", "text": "تمرين: حساب الطاقة الحركية", "link": "#"},
                        {"icon": "📝", "text": "تمرين: تحولات الطاقة", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: الطاقة في الحياة اليومية", "link": "#"},
                    ]
                }
            ]
        },
        "math_middle": {
            "title": "📗 كتاب الرياضيات - إعدادي",
            "description": "أساسيات الجبر والهندسة للمرحلة الإعدادية.",
            "theme_class": "math-middle-theme",
            "sections": [
                {
                    "title": "الوحدة 1: الجبر",
                    "items": [
                        {"icon": "📝", "text": "تمرين: حل المعادلات البسيطة", "link": "#"},
                        {"icon": "📝", "text": "تمرين: التناسب والتناسب العكسي", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: شرح المتغيرات", "link": "#"},
                    ]
                },
                {
                    "title": "الوحدة 2: الهندسة",
                    "items": [
                        {"icon": "📝", "text": "تمرين: المثلثات والزوايا", "link": "#"},
                        {"icon": "📝", "text": "تمرين: التحويلات الهندسية", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: الأشكال ثنائية الأبعاد", "link": "#"},
                    ]
                }
            ]
        },
        "chemistry_high": {
            "title": "📕 كتاب الكيمياء - ثانوي",
            "description": "مفاهيم متقدمة في الكيمياء للمرحلة الثانوية.",
            "theme_class": "chemistry-high-theme",
            "sections": [
                {
                    "title": "الوحدة 1: الجدول الدوري",
                    "items": [
                        {"icon": "📝", "text": "تمرين: تصنيف العناصر", "link": "#"},
                        {"icon": "📝", "text": "تمرين: خصائص المجموعات", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: تطور الجدول الدوري", "link": "#"},
                    ]
                },
                {
                    "title": "الوحدة 2: الروابط الكيميائية",
                    "items": [
                        {"icon": "📝", "text": "تمرين: الروابط التساهمية", "link": "#"},
                        {"icon": "📝", "text": "تمرين: الروابط الأيونية", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: أمثلة تفاعلية", "link": "#"},
                    ]
                }
            ]
        },
        "philosophy_high": {
            "title": "📕 كتاب الفلسفة - ثانوي",
            "description": "مقدمة إلى الفلسفة القديمة والحديثة.",
            "theme_class": "philosophy-high-theme",
            "sections": [
                {
                    "title": "الوحدة 1: الفلسفة القديمة",
                    "items": [
                        {"icon": "📝", "text": "تمرين: أفلاطون وأرسطو", "link": "#"},
                        {"icon": "📝", "text": "تمرين: مفاهيم الوجود والمعرفة", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: الفلسفة اليونانية", "link": "#"},
                    ]
                },
                {
                    "title": "الوحدة 2: الفلسفة الحديثة",
                    "items": [
                        {"icon": "📝", "text": "تمرين: ديكارت وكانط", "link": "#"},
                        {"icon": "📝", "text": "تمرين: نظرية المعرفة", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: العقل والتجربة", "link": "#"},
                    ]
                }
            ]
        },
        "stats_university": {
            "title": "📚 كتاب الإحصاء - جامعي",
            "description": "مدخل إلى علم الإحصاء وتحليل البيانات.",
            "theme_class": "stats-university-theme",
            "sections": [
                {
                    "title": "الوحدة 1: التوزيعات",
                    "items": [
                        {"icon": "📝", "text": "تمرين: التوزيع الطبيعي", "link": "#"},
                        {"icon": "📝", "text": "تمرين: التوزيع التكراري", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: أمثلة بيانية", "link": "#"},
                    ]
                },
                {
                    "title": "الوحدة 2: تحليل البيانات",
                    "items": [
                        {"icon": "📝", "text": "تمرين: الوسط والانحراف المعياري", "link": "#"},
                        {"icon": "📝", "text": "تمرين: الرسوم البيانية", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: إحصاء عملي", "link": "#"},
                    ]
                }
            ]
        },
        "psychology_university": {
            "title": "📚 كتاب علم النفس - جامعي",
            "description": "نظريات الشخصية والسلوك والتعلم.",
            "theme_class": "psychology-university-theme",
            "sections": [
                {
                    "title": "الوحدة 1: الشخصية والسلوك",
                    "items": [
                        {"icon": "📝", "text": "تمرين: تحليل أنماط الشخصية", "link": "#"},
                        {"icon": "📝", "text": "تمرين: قياس السلوكيات", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: مدارس علم النفس", "link": "#"},
                    ]
                },
                {
                    "title": "الوحدة 2: التعلم والذاكرة",
                    "items": [
                        {"icon": "📝", "text": "تمرين: تجارب بافلوف", "link": "#"},
                        {"icon": "📝", "text": "تمرين: نظرية التعلم الاجتماعي", "link": "#"},
                        {"icon": "🎥", "text": "فيديو: الذاكرة قصيرة وطويلة المدى", "link": "#"},
                    ]
                }
            ]
        },
    }

    book_data = books_data.get(book_name)
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

# ✅ نقطة نهاية التسجيل الجديدة
@app.post("/api/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register_user(user_in: UserIn):
    # التحقق من وجود اسم المستخدم أو البريد الإلكتروني
    existing_user = await User.find_one(
        (User.username == user_in.username) | (User.email == user_in.email)
    )
    if existing_user:
        raise ValidationError(
            message="اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل.",
            field="username_or_email",
            value=user_in.username # أو user_in.email
        )

    # إنشاء المستخدم
    user = await User.create_user(user_in)
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
    """
    نقطة نهاية محسنة تدعم البحث والتصفية بشكل كامل وصحيح.
    """
    allowed_content_types = ["book", "educational", "hadith"]
    if content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"نوع المحتوى غير صالح. الأنواع المدعومة هي: {', '.join(allowed_content_types)}"
        )

    query_conditions = {"content_type": content_type}
    tag_filters = []

    if q:
        # ✅ تفعيل البحث النصي - يتطلب فهرساً نصياً في نموذج BaseContent
        query_conditions["$text"] = {"$search": q}

    if content_type == "book" and category and category != "ALL":
        tag_filters.append(category)
    
    if content_type == "educational":
        if level and level != "ALL":
            tag_filters.append(level)
        if subject and subject != "ALL":
            tag_filters.append(subject)
        
    if tag_filters:
        query_conditions["tags"] = {"$all": tag_filters}
        
    content_list = await BaseContent.find(query_conditions)\
                                    .sort(-BaseContent.added_at)\
                                    .skip((page - 1) * page_size)\
                                    .limit(page_size)\
                                    .to_list()
    return content_list

@app.get("/api/content/{item_id}", response_model=BaseContent, tags=["Content"])
async def get_content_item(item_id: PydanticObjectId):
    """
    الحصول على تفاصيل عنصر محتوى معين.
    """
    content = await BaseContent.get(item_id)
    if not content:
        raise ContentNotFoundError(content_type="Content Item", content_id=str(item_id))
    return content

# ✅ إصلاح نقطة نهاية التلخيص
@app.post("/api/summarize/{item_id}", tags=["Content"])
async def summarize_content(item_id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    """
    إنشاء ملخص لمحتوى معين باستخدام Gemini API.
    """
    from app.services.gemini_utils import generate_gemini_summary 

    content = await BaseContent.get(item_id)
    if not content:
        raise ContentNotFoundError(content_type="Content Item", content_id=str(item_id))
    
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
    """
    إرسال تقييم وتعليق على محتوى معين.
    """
    content = await BaseContent.get(feedback_in.content_id)
    if not content:
        raise ContentNotFoundError(content_type="Content Item", content_id=str(feedback_in.content_id))

    feedback = Feedback(
        content_id=feedback_in.content_id,
        user_id=current_user.id,
        username=current_user.username,
        rating=feedback_in.rating,
        comment=feedback_in.comment
    )
    await feedback.insert()

    current_ratings = await Feedback.find(Feedback.content_id == feedback_in.content_id).to_list()
    total_rating = sum(f.rating for f in current_ratings)
    rating_count = len(current_ratings)
    
    await content.set({
        BaseContent.average_rating: total_rating / rating_count if rating_count > 0 else 0.0,
        BaseContent.rating_count: rating_count
    })

    return {"message": "تم إرسال التقييم بنجاح."}

@app.get("/api/feedback/{content_id}", response_model=List[Feedback], tags=["Feedback"])
async def get_feedback_for_content(content_id: PydanticObjectId):
    """
    الحصول على جميع التقييمات والتعليقات لمحتوى معين.
    """
    feedbacks = await Feedback.find(Feedback.content_id == content_id).sort(-Feedback.created_at).to_list()
    return feedbacks

@app.get("/api/admin/stats", tags=["Admin"])
async def get_admin_stats(current_user: User = Depends(get_current_admin_user)):
    """
    الحصول على إحصائيات لوحة تحكم المسؤول.
    """
    total_users = await User.count()
    total_content = await BaseContent.count()
    total_feedback = await Feedback.count()
    
    return {
        "total_users": total_users,
        "total_content": total_content,
        "total_feedback": total_feedback,
    }

# ✅ نقطة نهاية إدارة المحتوى (للمستخدمين الإداريين فقط)
# ✅ تم التعديل: استخدام ContentCreateIn بدلاً من BaseContent مباشرة
@app.post("/api/content", status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
async def create_content(content_data: ContentCreateIn, current_user: User = Depends(get_current_admin_user)):
    """إضافة محتوى جديد (للمسؤولين فقط)"""
    content = BaseContent(**content_data.dict())
    await content.insert()
    return content

@app.put("/api/content/{content_id}", tags=["Admin Content"])
async def update_content(content_id: PydanticObjectId, content_data: ContentUpdateIn, current_user: User = Depends(get_current_admin_user)):
    """تحديث محتوى موجود (للمسؤولين فقط)"""
    content = await BaseContent.get(content_id)
    if not content:
        raise ContentNotFoundError(content_type="Content Item", content_id=str(content_id))
    
    update_data = content_data.dict(exclude_unset=True)
    await content.set(update_data)
    return content

@app.delete("/api/content/{content_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
async def delete_content(content_id: PydanticObjectId, current_user: User = Depends(get_current_admin_user)):
    """حذف محتوى (للمسؤولين فقط)"""
    content = await BaseContent.get(content_id)
    if not content:
        raise ContentNotFoundError(content_type="Content Item", content_id=str(content_id))
    
    await content.delete()
    return
