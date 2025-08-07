from beanie import Document, PydanticObjectId, Indexed
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT

# --- نماذج Pydantic (للإدخال والإخراج في API) ---
class UserIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class FeedbackIn(BaseModel):
    content_id: PydanticObjectId
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=10, max_length=500)

class ContentCreateIn(BaseModel):
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    source: str
    source_id: str
    source_url: Optional[str] = None
    content_type: Literal["book", "educational", "hadith"]
    tags: List[str] = []
    language: Optional[str] = "ar"

class ContentUpdateIn(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    tags: Optional[List[str]] = None
    language: Optional[str] = None

# --- نماذج Beanie (للتخزين في قاعدة بيانات MongoDB) ---
class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None # للحذف الناعم

    class Settings:
        name = "users"

class BaseContent(Document):
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    source: str
    source_id: str
    source_url: Optional[str] = None
    content_type: str
    tags: List[str] = Field(default_factory=list)
    average_rating: float = 0.0
    rating_count: int = 0
    added_at: datetime = Field(default_factory=datetime.utcnow)
    language: str = "ar"
    deleted_at: Optional[datetime] = None # للحذف الناعم

    class Settings:
        name = "content"
        indexes = [
            # فهرس نصي للبحث بالاسم والوصف
            IndexModel(
                [("title", TEXT), ("description", TEXT)],
                name="title_desc_text_index",
                default_language="none" # يدعم لغات متعددة بشكل أفضل
            ),
            # فهرس مركب لتسريع الفلترة والترتيب الشائع
            IndexModel(
                [("content_type", ASCENDING), ("added_at", DESCENDING)],
                name="type_and_date_sort_index"
            ),
            # فهارس للحقول التي يتم البحث بها كثيراً
            IndexModel([("tags", ASCENDING)], name="tags_index"),
            IndexModel([("language", ASCENDING)], name="language_index"),
            IndexModel([("deleted_at", ASCENDING)], name="deleted_at_index", sparse=True), # فهرس متفرق للحذف الناعم
        ]

class Feedback(Document):
    content_id: Indexed(PydanticObjectId)
    user_id: Indexed(PydanticObjectId)
    username: str
    rating: int
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "feedbacks"
        indexes = [
            # فهرس مركب لجلب التعليقات مرتبة
            IndexModel(
                [("content_id", ASCENDING), ("created_at", DESCENDING)],
                name="feedback_query_index"
            )
        ]
