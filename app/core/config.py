# app/core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

class Settings(BaseSettings):
    """
    فئة لإدارة إعدادات التطبيق باستخدام Pydantic.
    تقوم بالتحقق من وجود المتغيرات وتحديد أنواعها.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # إعدادات قاعدة البيانات
    DB_URI: str
    DB_NAME: str

    # مفاتيح الواجهات البرمجية (API Keys)
    GEMINI_API_KEY: str
    GOOGLE_BOOKS_API_KEY: str
    # TMDB_API_KEY: str # ✅ مُعلّق لأنها غير مستخدمة
    YOUTUBE_API_KEY: str # ✅ مضاف

    # إعدادات التوثيق (Authentication) باستخدام JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # إعدادات عمال الخلفية (Workers)
    NUM_WORKERS: int = 4
    CYCLE_WAIT_MINUTES: int = 60
    REQUEST_TIMEOUT: int = 30 # ✅ مضاف
    MAX_RETRIES: int = 3 # ✅ مضاف
    RETRY_DELAY: int = 2 # ✅ مضاف

# إنشاء نسخة واحدة من الإعدادات لاستخدامها في كل المشروع
settings = Settings()
