# workers/hadith_worker.py
import asyncio
import logging
# ✅ استيراد دوال التطبيع من worker_utils
from workers.worker_utils import normalize_archive_item
# ✅ استيراد دوال الجلب من worker_utils
from workers.fetchers import fetch_internet_archive

async def hadith_task_generator(queue: asyncio.Queue):
    # ✅ استخدام مصطلحات بحث أكثر تنوعاً لضمان وجود نتائج
    queries = [
        "صحيح البخاري", "صحيح مسلم", "شرح رياض الصالحين",
        "سنن الترمذي", "الأربعون النووية", "مسند أحمد",
        "الترغيب والترهيب", "المنهاج في الحديث"
    ]
    logging.info(f"Hadith Worker: Starting cycle for queries: {queries}")
    for query in queries:
        try:
            # نبحث عن مواد صوتية لأنها الأنسب للأحاديث
            archive_data = await fetch_internet_archive(query, media_type="audio", max_results=15) # ✅ زيادة عدد النتائج
            for item in archive_data:
                # ✅ التأكد من تعيين النوع الصحيح "hadith"
                normalized_data = normalize_archive_item(item, "hadith")
                # ✅ التأكد من أن الحقول الأساسية موجودة
                if normalized_data["title"] and normalized_data["source_id"]:
                    normalized_data["tags"].append("حديث")
                    await queue.put(normalized_data)
        except Exception as e:
            logging.error(f"Hadith Worker Error for query '{query}': {e}")
