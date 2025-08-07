import os
import httpx
import logging
from typing import List, Dict, Any
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")

# ✅ تحديث: إزالة دوال جلب الأفلام والبودكاست
# async def fetch_tmdb_films(query: str, lang: str = 'ar-SA', max_results: int = 5) -> List[Dict[str, Any]]:
#     api_key = os.getenv("TMDB_API_KEY")
#     if not api_key:
#         logging.warning("TMDB_API_KEY not found. Skipping TMDb fetch.")
#         return []
#     logging.info(f"TMDb: Searching for films matching '{query}' in lang '{lang}'...")
#     url = "https://api.themoviedb.org/3/search/movie"
#     params = {"api_key": api_key, "query": quote(query), "language": lang, "include_adult": "false"}
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url, params=params)
#             response.raise_for_status()
#             return response.json().get('results', [])[:max_results]
#     except Exception as e:
#         logging.error(f"Failed to fetch from TMDb for query '{query}': {e}")
#     return []

async def fetch_google_books(query: str, lang: str = 'ar', max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الكتب من Google Books API.
    """
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if not api_key:
        logging.warning("GOOGLE_BOOKS_API_KEY not found. Skipping Google Books fetch.")
        return []
    logging.info(f"Google Books: Searching for books matching '{query}' in lang '{lang}'...")
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": quote(query), "key": api_key, "langRestrict": lang, "maxResults": max_results}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get('items', [])
    except Exception as e:
        logging.error(f"Failed to fetch from Google Books for query '{query}': {e}")
    return []

async def fetch_open_library_books(query: str, lang: str = 'ara', max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الكتب من Open Library API.
    """
    logging.info(f"Open Library: Searching for books matching '{query}' in lang '{lang}'...")
    url = "https://openlibrary.org/search.json"
    params = {"q": quote(query), "limit": max_results, "language": lang}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get('docs', [])
    except Exception as e:
        logging.error(f"Failed to fetch from Open Library for query '{query}': {e}")
    return []

# ✅ تحديث: إزالة دوال جلب الأفلام والبودكاست
# async def fetch_itunes_podcasts(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
#     """
#     جلب البودكاست من iTunes API.
#     """
#     logging.info(f"iTunes: Searching for podcasts matching '{query}'...")
#     url = "https://itunes.apple.com/search"
#     params = {"term": quote(query), "media": "podcast", "limit": max_results, "entity": "podcast"}
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url, params=params)
#             response.raise_for_status()
#             return response.json().get('results', [])
#     except Exception as e:
#         logging.error(f"Failed to fetch from iTunes for query '{query}': {e}")
#     return []

async def fetch_internet_archive(query: str, media_type: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب المحتوى من Internet Archive API بناءً على نوع الوسائط.
    """
    logging.info(f"Internet Archive: Searching for '{media_type}' matching '{query}'...")
    url = "https://archive.org/advancedsearch.php"
    params = {
        "q": quote(query),
        "output": "json",
        "rows": max_results,
        "fl[]": "identifier,title,description,creator,date,subject,mediatype",
        "sort[]": "downloads desc"
    }
    # إضافة فلتر نوع الوسائط إذا تم تحديده
    if media_type:
        params["fq[]"] = f"mediatype:({media_type})"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get('response', {}).get('docs', [])
    except Exception as e:
        logging.error(f"Failed to fetch from Internet Archive for query '{query}' (type: {media_type}): {e}")
    return []

async def fetch_youtube_videos(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    جلب الفيديوهات من YouTube API (يمكن استخدامها للدروس).
    """
    api_key = os.getenv("YOUTUBE_API_KEY") # افتراض وجود مفتاح API لليوتيوب
    if not api_key:
        logging.warning("YOUTUBE_API_KEY not found. Skipping YouTube fetch.")
        return []
    logging.info(f"YouTube: Searching for videos matching '{query}'...")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "q": quote(query),
        "key": api_key,
        "part": "snippet",
        "type": "video",
        "maxResults": max_results
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get('items', [])
    except Exception as e:
        logging.error(f"Failed to fetch from YouTube for query '{query}': {e}")
    return []

