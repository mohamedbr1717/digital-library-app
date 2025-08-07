# workers/education_worker.py
import asyncio
import logging
# ✅ استيراد دوال التطبيع من worker_utils
from workers.worker_utils import normalize_youtube_video
# ✅ استيراد دوال الجلب من worker_utils
from workers.fetchers import fetch_youtube_videos

async def add_static_educational_books(queue: asyncio.Queue):
    """
    دالة لإضافة الكتب المدرسية الثابتة إلى طابور المهام.
    """
    logging.info("Education Worker: Adding static educational books to the queue...")
    static_books = [
        {
            "title": "📘 كتاب اللغة العربية - ابتدائي", "description": "أساسيات اللغة العربية للمرحلة الابتدائية.",
            "source_url": "/books/arabic_primary", "level": "الابتدائي", "subject": "اللغة العربية"
        },
        {
            "title": "📗 كتاب الفيزياء - إعدادي", "description": "مبادئ الفيزياء للمرحلة الإعدادية.",
            "source_url": "/books/physics_middle", "level": "الإعدادي", "subject": "الفيزياء"
        },
        {
            "title": "📗 كتاب الرياضيات - إعدادي", "description": "أساسيات الجبر والهندسة للمرحلة الإعدادية.",
            "source_url": "/books/math_middle", "level": "الإعدادي", "subject": "الرياضيات"
        },
        {
            "title": "📕 كتاب الكيمياء - ثانوي", "description": "مفاهيم متقدمة في الكيمياء للمرحلة الثانوية.",
            "source_url": "/books/chemistry_high", "level": "الثانوي", "subject": "الكيمياء"
        },
        {
            "title": "📕 كتاب الفلسفة - ثانوي", "description": "مقدمة إلى الفلسفة القديمة والحديثة.",
            "source_url": "/books/philosophy_high", "level": "الثانوي", "subject": "الفلسفة"
        },
        {
            "title": "📚 كتاب الإحصاء - جامعي", "description": "مدخل إلى علم الإحصاء وتحليل البيانات.",
            "source_url": "/books/stats_university", "level": "الجامعي", "subject": "الإحصاء"
        },
        {
            "title": "📚 كتاب علم النفس - جامعي", "description": "نظريات الشخصية والسلوك والتعلم.",
            "source_url": "/books/psychology_university", "level": "الجامعي", "subject": "علم النفس"
        },
    ]

    for book in static_books:
        book_data = {
            "title": book["title"], "description": book["description"],
            "thumbnail": None, "source": "المكتبة الرقمية",
            "source_id": book["source_url"], "source_url": book["source_url"],
            "content_type": "educational",
            "tags": ["كتاب مدرسي", book["level"], book["subject"]],
            "language": "ar"
        }
        await queue.put(book_data)
    logging.info(f"Education Worker: Added {len(static_books)} static books.")


async def educational_task_generator(queue: asyncio.Queue):
    """
    الدالة الرئيسية لعامل الدروس: تضيف الكتب الثابتة ثم تبحث عن فيديوهات.
    """
    await add_static_educational_books(queue)

    # ✅ توسيع المواد والمستويات
    subjects = [
        "الرياضيات", "الفيزياء", "الكيمياء", "علوم الحياة والأرض", "اللغة العربية",
        "اللغة الفرنسية", "اللغة الإنجليزية", "الفلسفة", "التاريخ", "الجغرافيا",
        "البرمجة", "علم النفس", "الاقتصاد", "السياسة"
    ]
    levels = ["الابتدائي", "الإعدادي", "الثانوي", "الجامعي"]
    query_types = ["شرح درس", "تمارين وحلول", "مراجعة شاملة"]

    queries = [
        {"query": f"{qtype} {subject} للمستوى {level}", "level": level, "subject": subject, "type": qtype}
        for level in levels for subject in subjects for qtype in query_types
    ]

    logging.info(f"Education Worker: Starting to fetch videos for {len(queries)} detailed queries...")
    
    seen_ids = set()
    for item in queries:
        query = item["query"]
        try:
            videos_data = await fetch_youtube_videos(query, max_results=5)
            for video in videos_data:
                video_id = video.get("id", {}).get("videoId")
                if not video_id or video_id in seen_ids:
                    continue
                seen_ids.add(video_id)
                
                normalized_data = normalize_youtube_video(video, "educational")
                
                # ✅ التأكد من أن الحقول الأساسية موجودة
                if normalized_data["title"] and normalized_data["source_id"]:
                    additional_tags = ["فيديو تعليمي", item["level"], item["subject"], item["type"]]
                    if not isinstance(normalized_data.get("tags"), list):
                        normalized_data["tags"] = []
                    normalized_data["tags"].extend(additional_tags)
                    await queue.put(normalized_data)
                await asyncio.sleep(0.5)

        except Exception as e:
            logging.error(f"Education Worker: Error processing query '{query}': {e}")
    
    logging.info(f"Education Worker: Cycle finished. Total unique videos queued: {len(seen_ids)}")
