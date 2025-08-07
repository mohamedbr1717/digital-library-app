# workers/fetchers.py
import aiohttp
import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# تحميل الإعدادات من ملف .env
load_dotenv()

# --- إعدادات النظام ---
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
WORLDCAT_KEY = os.getenv("WORLDCAT_KEY")
LOC_CONGRESS_API_KEY = os.getenv("LOC_CONGRESS_API_KEY")

# --- تهيئة السجل ---
logger = logging.getLogger("fetchers")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# --- دوال جلب البيانات العامة ---
async def fetch_data(
    url: str, 
    params: Optional[Dict[str, Any]] = None, 
    headers: Optional[Dict[str, str]] = None,
    retries: int = MAX_RETRIES
) -> Optional[Dict[str, Any]]:
    """جلب البيانات من API مع إعادة المحاولة"""
    headers = headers or {}
    headers.setdefault("User-Agent", USER_AGENT)
    params = params or {}
    
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(1, retries + 1):
            try:
                async with session.get(
                    url, 
                    params=params, 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            # محاولة قراءة النص في حال لم يكن JSON
                            text_data = await response.text()
                            logger.warning(f"Received non-JSON response from {url}: {text_data[:100]}...")
                            return {"text": text_data}
                    logger.warning(f"فشل الطلب #{attempt} إلى {url}: الحالة {response.status}")
                    if response.status >= 500 and attempt < retries:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                    return None
            except asyncio.TimeoutError:
                logger.warning(f"انتهت مهلة الطلب #{attempt} إلى {url}")
                if attempt < retries:
                    await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"خطأ في جلب البيانات من {url}: {str(e)}")
                # لا نعيد المحاولة في حالة الأخطاء العامة
                return None
        return None

# --- دوال جلب الكتب ---
async def fetch_google_books(query: str, lang: str = 'ar', max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الكتب من Google Books API.
    """
    if not GOOGLE_BOOKS_API_KEY:
        logger.warning("GOOGLE_BOOKS_API_KEY not found. Skipping Google Books fetch.")
        return []
    logger.info(f"Google Books: Searching for books matching '{query}' in lang '{lang}'...")
    
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "key": GOOGLE_BOOKS_API_KEY,
        "langRestrict": lang,
        "maxResults": max_results
    }
    try:
        data = await fetch_data(url, params=params)
        if data and "items" in data: # ✅ تم تصحيح هذا السطر
            # إرجاع قائمة بعناصر volumeInfo مباشرة
            return [item.get("volumeInfo", {}) for item in data["items"]]
        else:
            logger.info(f"No 'items' found in Google Books response for query '{query}'.")
    except Exception as e:
        logger.error(f"Failed to fetch/process from Google Books for query '{query}': {e}")
    return []

async def fetch_open_library_books(query: str, lang: str = 'ara', max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الكتب من Open Library API.
    """
    logger.info(f"Open Library: Searching for books matching '{query}' in lang '{lang}'...")
    url = "https://openlibrary.org/search.json"
    params = {"q": query, "limit": max_results, "language": lang}
    try:
        data = await fetch_data(url, params=params)
        if data and "docs" in data: # ✅ تم تصحيح هذا السطر
            return data["docs"]
        else:
            logger.info(f"No 'docs' found in Open Library response for query '{query}'.")
    except Exception as e:
        logger.error(f"Failed to fetch/process from Open Library for query '{query}': {e}")
    return []

# --- دوال جلب الكتب من مصادر إضافية ---
async def fetch_worldcat_books(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الكتب من WorldCat Search API.
    """
    if not WORLDCAT_KEY:
        logger.warning("WORLDCAT_KEY not found. Skipping WorldCat fetch.")
        return []
    logger.info(f"WorldCat: Searching for books matching '{query}'...")
    
    url = "https://worldcat.org/webservices/catalog/search/worldcat/opensearch"
    params = {
        "q": query,
        "format": "json",
        "wskey": WORLDCAT_KEY,
        "count": max_results
    }
    try:
        data = await fetch_data(url, params=params)
        if data and "feed" in data and "entry" in data["feed"]:
            return data["feed"]["entry"]
        else:
            logger.info(f"No 'feed.entry' found in WorldCat response for query '{query}'.")
    except Exception as e:
        logger.error(f"Failed to fetch/process from WorldCat for query '{query}': {e}")
    return []

async def fetch_loc_books(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الكتب من Library of Congress API.
    """
    if not LOC_CONGRESS_API_KEY:
        logger.warning("LOC_CONGRESS_API_KEY not found. Skipping LOC fetch.")
        return []
    logger.info(f"Library of Congress: Searching for books matching '{query}'...")
    
    url = "https://www.loc.gov/books/"
    params = {
        "fo": "json",
        "q": query,
        "apikey": LOC_CONGRESS_API_KEY,
        "c": max_results
    }
    try:
        data = await fetch_data(url, params=params)
        if data and "results" in data:
            return data["results"]
        else:
            logger.info(f"No 'results' found in LOC response for query '{query}'.")
    except Exception as e:
        logger.error(f"Failed to fetch/process from Library of Congress for query '{query}': {e}")
    return []

# --- دوال جلب المواد التعليمية والأحاديث ---
async def fetch_internet_archive(query: str, media_type: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب المحتوى من Internet Archive API بناءً على نوع الوسائط.
    """
    logger.info(f"Internet Archive: Searching for '{media_type}' matching '{query}'...")
    url = "https://archive.org/advancedsearch.php"
    params = {
        "q": query,
        "output": "json",
        "rows": max_results,
        "fl[]": "identifier,title,description,creator,date,subject,mediatype",
        "sort[]": "downloads desc"
    }
    # إضافة فلتر نوع الوسائط إذا تم تحديده
    if media_type:
        params["fq[]"] = f"mediatype:({media_type})"

    try:
        data = await fetch_data(url, params=params)
        if data and "response" in data and "docs" in data["response"]:
            return data["response"]["docs"]
        else:
            logger.info(f"No valid 'response.docs' found in Internet Archive response for query '{query}' (type: {media_type}).")
    except Exception as e:
        logger.error(f"Failed to fetch/process from Internet Archive for query '{query}' (type: {media_type}): {e}")
    return []

async def fetch_youtube_videos(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الفيديوهات من YouTube API (يمكن استخدامها للدروس).
    """
    if not YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY not found. Skipping YouTube fetch.")
        return []
    logger.info(f"YouTube: Searching for videos matching '{query}'...")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "q": query,
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "type": "video",
        "maxResults": max_results
    }
    try:
        data = await fetch_data(url, params=params)
        if data and "items" in data:
            return data["items"]
        else:
           logger.info(f"No 'items' found in YouTube response for query '{query}'.")
    except Exception as e:
        logger.error(f"Failed to fetch/process from YouTube for query '{query}': {e}")
    return []
