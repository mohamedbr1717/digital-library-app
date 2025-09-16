# app/services/user_service.py
from app.db.models import User, UserIn, BaseContent # ✅ استيراد BaseContent
from app.db.error_models import ValidationError
from app.core.security import get_password_hash

class UserService:
    @staticmethod
    async def create_user(user_in: UserIn) -> User:
        # التحقق من وجود اسم المستخدم أو البريد الإلكتروني
        existing_user = await User.find_one(
            (User.username == user_in.username) | (User.email == user_in.email)
        )
        if existing_user:
            field = "username" if existing_user.username == user_in.username else "email"
            raise ValidationError(
                message="اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل.",
                field=field,
                value=user_in.username
            )
        
        # تشفير كلمة المرور وإنشاء المستخدم
        hashed_password = get_password_hash(user_in.password)
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password
        )
        await user.insert()
        return user

    @staticmethod
    async def get_admin_stats():
        """
        يجلب إحصائيات بسيطة للوحة تحكم المدير.
        """
        total_users = await User.find({"deleted_at": None}).count()
        # ✅ تصحيح استيراد واستخدام BaseContent
        total_content = await BaseContent.find({"deleted_at": None}).count()
        total_feedback = await Feedback.count()
        
        return {
            "total_users": total_users,
            "total_content": total_content,
            "total_feedback": total_feedback,
        }
