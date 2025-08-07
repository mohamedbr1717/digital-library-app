from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
import traceback
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

# --- أنواع الأخطاء والتصنيفات ---

class ErrorType(str, Enum):
    VALIDATION = "validation_error"
    DATABASE = "database_error"
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    NOT_FOUND = "not_found_error"
    EXTERNAL_SERVICE = "external_service_error"
    SERVER_ERROR = "internal_server_error"

class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# --- نماذج Pydantic لهيكلة الأخطاء ---

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    value: Optional[Any] = None

class APIErrorResponse(BaseModel):
    type: ErrorType
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)
    request_id: Optional[str] = None

# --- نموذج Beanie لتسجيل الأخطاء في قاعدة البيانات ---

class ErrorLog(Document):
    """نموذج لتخزين تفاصيل الأخطاء في MongoDB للمراجعة لاحقاً."""
    error_type: ErrorType
    severity: ErrorSeverity = ErrorSeverity.MEDIUM # ✅ قيمة افتراضية للشدة
    message: str
    stack_trace: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    user_id: Optional[PydanticObjectId] = None
    request_id: Optional[str] = None
    # ✅ تم التعديل: التفاصيل الآن قائمة من ErrorDetail
    details: List[ErrorDetail] = Field(default_factory=list) 
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False

    class Settings:
        name = "error_logs"

# --- استثناءات مخصصة (Custom Exceptions) ---

class LibraryException(Exception):
    """الاستثناء الأساسي في التطبيق."""
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.SERVER_ERROR,
        status_code: int = 500,
        details: List[ErrorDetail] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM # ✅ إضافة مستوى الشدة
    ):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or []
        self.severity = severity # ✅ تعيين مستوى الشدة
        super().__init__(self.message)

class ValidationError(LibraryException):
    # ✅ تم التعديل: يمكن أن تستقبل رسالة واحدة أو تفاصيل متعددة
    def __init__(self, message: str = "Validation failed", field: str = None, value: Any = None, details: Optional[List[ErrorDetail]] = None):
        if not details and (field or message):
            details = [ErrorDetail(field=field, message=message, value=value)]
        elif not details:
            details = []
        super().__init__(message, ErrorType.VALIDATION, 400, details, ErrorSeverity.LOW) # ✅ تحديد الشدة

class DatabaseError(LibraryException):
    def __init__(self, message: str):
        super().__init__(message, ErrorType.DATABASE, 500, severity=ErrorSeverity.CRITICAL) # ✅ تحديد الشدة

class AuthenticationError(LibraryException):
    def __init__(self, message: str = "بيانات الدخول غير صحيحة"):
        super().__init__(message, ErrorType.AUTHENTICATION, 401, severity=ErrorSeverity.MEDIUM) # ✅ تحديد الشدة

class AuthorizationError(LibraryException):
    def __init__(self, message: str = "ليس لديك الصلاحية للوصول"):
        super().__init__(message, ErrorType.AUTHORIZATION, 403, severity=ErrorSeverity.HIGH) # ✅ تحديد الشدة

class ContentNotFoundError(LibraryException):
    # ✅ تم التعديل: رسالة عامة أفضل وإمكانية تحديد النوع والمعرف
    def __init__(self, message: str = "المحتوى المطلوب غير موجود.", content_type: Optional[str] = None, content_id: Optional[str] = None):
        full_message = message
        if content_type and content_id:
            full_message = f"المحتوى من نوع '{content_type}' بالمعرف '{content_id}' غير موجود."
        elif content_id:
            full_message = f"المحتوى بالمعرف '{content_id}' غير موجود."
        super().__init__(full_message, ErrorType.NOT_FOUND, 404, severity=ErrorSeverity.LOW) # ✅ تحديد الشدة

class ExternalServiceError(LibraryException):
    def __init__(self, service_name: str, message: str):
        full_message = f"خطأ في الخدمة الخارجية ({service_name}): {message}"
        super().__init__(full_message, ErrorType.EXTERNAL_SERVICE, 503, severity=ErrorSeverity.HIGH) # ✅ تحديد الشدة
