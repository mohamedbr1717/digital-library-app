import os
import httpx
import logging
from typing import List, Dict, Any
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")

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
    api_key = os.getenv("YOUTUBE_API_KEY")
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
