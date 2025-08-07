from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import settings
from ..db.models import User  # استيراد نموذج المستخدم للبحث في قاعدة البيانات

# إعداد مخطط التوثيق
# هذا يخبر FastAPI من أين يقرأ التوكن (من هيدر Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# إعداد سياق تشفير كلمة المرور
# نستخدم bcrypt لأنه خوارزمية قوية وآمنة
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    التحقق من تطابق كلمة المرور المدخلة مع النسخة المشفرة.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    تشفير كلمة مرور جديدة.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    إنشاء رمز دخول (JWT) جديد.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    فك تشفير التوكن، التحقق من صلاحيته، وإرجاع بيانات المستخدم.
    هذه الدالة تستخدم كـ "Dependency" في نقاط النهاية المحمية.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await User.find_one(User.username == username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    دالة تعتمد على الدالة السابقة وتتحقق إذا كان المستخدم مديراً.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have admin privileges"
        )
    return current_user

