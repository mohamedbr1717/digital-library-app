import asyncio
import logging
import signal
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# --- استيراد من ملفات المشروع ---
# هذا الجزء مهم جداً ويعمل فقط إذا كان مجلد workers في المكان الصحيح
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings
from app.db.models import User, BaseContent, Feedback
from app.db.error_models import ErrorLog

# ✅ الإصلاح: إزالة استيراد عمال البودكاست والفيديو
from workers.book_worker import book_task_generator
from workers.education_worker import educational_task_generator
from workers.hadith_worker import hadith_task_generator


# --- إعداد نظام التسجيل (Logging) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s",
    handlers=[
        logging.FileHandler("workers.log"),
        logging.StreamHandler()
    ]
)

async def main_task_generator(queue: asyncio.Queue):
    """
    الدالة الرئيسية التي تقوم بتشغيل جميع مولدات المهام بشكل دوري.
    """
    while True:
        try:
            logging.info("🚀 Starting new data fetching cycle...")
            
            # إنشاء وتشغيل جميع مولدات المهام في نفس الوقت
            await asyncio.gather(
                # ✅ إزالة audio_task_generator
                book_task_generator(queue),
                educational_task_generator(queue),
                hadith_task_generator(queue),
                # ✅ إزالة video_task_generator
            )
            
            logging.info(f"✅ Cycle finished. Waiting for {settings.CYCLE_WAIT_MINUTES} minutes...")
            await asyncio.sleep(settings.CYCLE_WAIT_MINUTES * 60)
            
        except asyncio.CancelledError:
            logging.info("🛑 Task generator received shutdown signal.")
            break
        except Exception as e:
            logging.error(f"🔥 An error occurred in the main task generator: {e}", exc_info=True)
            await asyncio.sleep(60) # الانتظار قليلاً قبل إعادة المحاولة

async def worker(name: str, queue: asyncio.Queue):
    """
    عامل يقوم بسحب المهام من الطابور ومعالجتها.
    """
    while True:
        try:
            task_data = await queue.get()
            logging.info(f"🏗️ Worker '{name}' started processing task: {task_data.get('title', 'N/A')}")
            
            # ✅ منطق حفظ المحتوى في قاعدة البيانات
            # التأكد من عدم وجود المحتوى مسبقاً بنفس المصدر والمعرف
            existing_content = await BaseContent.find_one(
                BaseContent.source == task_data.get("source"),
                BaseContent.source_id == task_data.get("source_id")
            )
            
            if not existing_content:
                content = BaseContent(**task_data)
                await content.insert()
                logging.info(f"💾 Worker '{name}' saved new content: {content.title}")
            else:
                logging.info(f"⏭️ Worker '{name}' skipped duplicate content: {task_data.get('title')}")

            queue.task_done()
            
        except asyncio.CancelledError:
            logging.info(f"🛑 Worker '{name}' received shutdown signal.")
            break
        except Exception as e:
            logging.error(f"🔥 Worker '{name}' encountered an error processing task: {e}", exc_info=True)


async def main():
    """
    الدالة الرئيسية لتشغيل نظام العمال.
    """
    logging.info("⚙️ Initializing workers system...")
    
    # الاتصال بقاعدة البيانات
    client = AsyncIOMotorClient(settings.DB_URI)
    await init_beanie(
        database=client[settings.DB_NAME],
        document_models=[User, BaseContent, Feedback, ErrorLog]
    )
    logging.info("✅ Database connected for workers.")
    
    task_queue = asyncio.Queue(maxsize=200)
    
    # بدء مولد المهام الرئيسي
    generator_task = asyncio.create_task(main_task_generator(task_queue))
    
    # بدء العمال
    worker_tasks = [
        asyncio.create_task(worker(f"worker-{i}", task_queue)) # ✅ تم تصحيح f-string هنا
        for i in range(settings.NUM_WORKERS)
    ]
    
    await asyncio.gather(generator_task, *worker_tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("⏹️ Workers system stopped manually.")

