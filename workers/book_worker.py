# workers/book_worker.py
import asyncio
import logging
# ✅ استيراد دوال التطبيع من worker_utils
from workers.worker_utils import (
    normalize_google_book, 
    normalize_open_library_book,
    normalize_worldcat_book,
    normalize_loc_book,
    normalize_archive_item
)
# ✅ استيراد دوال الجلب من fetchers
from workers.fetchers import (
    fetch_google_books, 
    fetch_open_library_books, 
    fetch_worldcat_books,
    fetch_loc_books,
    fetch_internet_archive
)

async def book_task_generator(queue: asyncio.Queue):
    # ✅ توسيع الاستعلامات
    queries = [
        "history", "science", "literature", "philosophy", "programming", "novels",
        "Quran", "Hadith", "Fiqh", "Seerah", 
        "psychology", "economics", "politics"
    ]
    
    # ✅ قائمة اللغات المدعومة
    languages = ["ar", "en", "fr", "es", "de"] # يمكنك إضافة المزيد من اللغات حسب الحاجة

    logging.info(f"Book Worker: Starting cycle for {len(queries)} queries in {len(languages)} languages.")
    
    seen_ids = set()

    for query in queries:
        for lang in languages:
            try:
                # --- جلب البيانات من كل المصادر بالتوازي ---
                google_results, open_lib_results, worldcat_results, loc_results, archive_results = await asyncio.gather(
                    fetch_google_books(query, lang=lang, max_results=10),
                    fetch_open_library_books(query, lang=lang, max_results=10),
                    fetch_worldcat_books(query, max_results=10),
                    fetch_loc_books(query, max_results=10),
                    fetch_internet_archive(query, media_type="texts", max_results=10)
                )

                # --- معالجة نتائج Google Books ---
                for item in google_results:
                    book_id = f"google_{item.get('id')}"
                    if book_id and book_id not in seen_ids:
                        seen_ids.add(book_id)
                        normalized_data = normalize_google_book(item)
                        # ✅ التأكد من أن الحقول الأساسية موجودة
                        if normalized_data["title"] and normalized_data["source_id"]:
                            normalized_data["tags"].append(query)
                            await queue.put(normalized_data)

                # --- معالجة نتائج Open Library ---
                for item in open_lib_results:
                    book_id = f"openlib_{item.get('key')}"
                    if book_id and book_id not in seen_ids:
                        seen_ids.add(book_id)
                        normalized_data = normalize_open_library_book(item)
                        if normalized_data["title"] and normalized_data["source_id"]:
                            normalized_data["tags"].append(query)
                            await queue.put(normalized_data)

                # --- معالجة نتائج WorldCat ---
                for item in worldcat_results:
                    book_id = f"worldcat_{item.get('id')}"
                    if book_id and book_id not in seen_ids:
                        seen_ids.add(book_id)
                        normalized_data = normalize_worldcat_book(item)
                        if normalized_data["title"] and normalized_data["source_id"]:
                            normalized_data["tags"].append(query)
                            await queue.put(normalized_data)

                # --- معالجة نتائج Library of Congress ---
                for item in loc_results:
                    book_id = f"loc_{item.get('id')}"
                    if book_id and book_id not in seen_ids:
                        seen_ids.add(book_id)
                        normalized_data = normalize_loc_book(item)
                        if normalized_data["title"] and normalized_data["source_id"]:
                            normalized_data["tags"].append(query)
                            await queue.put(normalized_data)

                # --- معالجة نتائج Internet Archive ---
                for item in archive_results:
                    book_id = f"archive_{item.get('identifier')}"
                    if book_id and book_id not in seen_ids:
                        seen_ids.add(book_id)
                        normalized_data = normalize_archive_item(item, "book")
                        if normalized_data["title"] and normalized_data["source_id"]:
                            normalized_data["tags"].append(query)
                            await queue.put(normalized_data)
                
                await asyncio.sleep(1) # انتظار بسيط بين الاستعلامات

            except Exception as e:
                logging.error(f"Book Worker: Error for query '{query}' in '{lang}': {e}")

    logging.info(f"Book Worker: Cycle finished. Total unique books queued: {len(seen_ids)}")
