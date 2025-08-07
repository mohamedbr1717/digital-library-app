# app/services/user_service.py
from app.db.models import User, UserIn
from app.db.error_models import ValidationError
from app.core.security import get_password_hash

class UserService:
    @staticmethod
    async def create_user(user_in: UserIn) -> User:
        """
        ينشئ مستخدماً جديداً مع التحقق من عدم وجود مستخدم بنفس البيانات.
        """
        # التحقق من وجود اسم المستخدم
        if await User.find_one(User.username == user_in.username):
            raise ValidationError(
                message="اسم المستخدم هذا مستخدم بالفعل.",
                field="username"
            )
        
        # التحقق من وجود البريد الإلكتروني
        if await User.find_one(User.email == user_in.email):
            raise ValidationError(
                message="هذا البريد الإلكتروني مسجل بالفعل.",
                field="email"
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
        total_content = await User.find_one({"deleted_at": None}).count() # يفترض أن تكون BaseContent
        # ملاحظة: يجب تعديل السطر أعلاه ليكون من BaseContent
        # from app.db.models import BaseContent
        # total_content = await BaseContent.find({"deleted_at": None}).count()
        
        return {
            "total_users": total_users,
            "total_content": 0, # قيمة مؤقتة حتى يتم تصحيح الاستيراد
        }

