# workers/worker_utils.py
import re
import logging
from typing import Any, List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("worker_utils")

def sanitize_string(value: Any) -> str:
    """تنظيف وتنسيق السلاسل النصية"""
    if value is None:
        return ""
    if isinstance(value, list) and not value: # إذا كانت قائمة فارغة، أرجع سلسلة فارغة
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = re.sub(r'\s+', ' ', value).strip()
    # ✅ تقليل قيود التنظيف لتجنب فقدان البيانات
    # value = re.sub(r'[^\w\s.,!?;:()\[\]{}@#$%^&*+=/\'"\-–—]', '', value)
    return value

def parse_year(date_str: str) -> Optional[int]:
    """تحويل تاريخ إلى سنة"""
    if not date_str:
        return None
    try:
        match = re.search(r'\b(\d{4})\b', date_str)
        if match:
            year = int(match.group(1))
            if 1000 <= year <= datetime.now().year:
                return year
    except (ValueError, TypeError):
        pass
    return None

def _ensure_list(value: Any) -> List[str]:
    """تحويل قيمة إلى قائمة من السلاسل"""
    if value is None: return []
    if isinstance(value, list): return [str(item).strip() for item in value if item is not None and str(item).strip()]
    if isinstance(value, str): return [tag.strip() for tag in value.replace(',', ';').split(';') if tag.strip()]
    try: return [str(value).strip()]
    except: return []

# --- دوال التطبيع ---
def normalize_google_book(item: Dict[str, Any]) -> Dict[str, Any]:
    info = item.get('volumeInfo', {})
    return {
        "title": sanitize_string(info.get("title", "No Title")),
        "description": sanitize_string(info.get("description", ""))[:500],
        "thumbnail": sanitize_string(info.get("imageLinks", {}).get("thumbnail", "")), # ✅ تم التعديل
        "source": "Google Books",
        "source_id": str(item.get("id", "")),
        "source_url": info.get("infoLink", ""),
        "content_type": "book",
        "tags": _ensure_list(info.get("categories", [])),
        "language": info.get("language", "ar"),
        "authors": _ensure_list(info.get("authors", [])),
    }

def normalize_open_library_book(item: Dict[str, Any]) -> Dict[str, Any]:
    """تطبيع بيانات كتاب من Open Library."""
    cover_id = item.get('cover_i')
    return {
        "title": sanitize_string(item.get("title", "No Title")),
        "description": sanitize_string(item.get("first_sentence", [None])[0] if isinstance(item.get("first_sentence"), list) else item.get("first_sentence", ""))[:500],
        "thumbnail": sanitize_string(f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""), # ✅ تم التعديل
        "source": "Open Library",
        "source_id": str(item.get("key", "").split("/")[-1] if item.get("key") else ""),
        "source_url": f"https://openlibrary.org{item.get('key', '')}",
        "content_type": "book",
        "tags": _ensure_list(item.get("subject", [])),
        "language": item.get("languages", [{}])[0].get("key", "").replace("/languages/", "") if item.get("languages") else "ar",
        "authors": _ensure_list(item.get("author_name", [])),
    }

# --- دوال تطبيع الكتب من مصادر إضافية ---
def normalize_worldcat_book(item: Dict[str, Any]) -> Dict[str, Any]:
    """تطبيع بيانات كتاب من WorldCat."""
    return {
        "title": sanitize_string(item.get("title", "No Title")),
        "description": sanitize_string(item.get("summary", ""))[:500],
        "thumbnail": sanitize_string(item.get("thumbnail", "")), # ✅ تم التعديل
        "source": "WorldCat",
        "source_id": str(item.get("id", "")),
        "source_url": item.get("link", {}).get("href", ""),
        "content_type": "book",
        "tags": _ensure_list(item.get("category", [])),
        "language": "ar",
        "authors": _ensure_list(item.get("author", [])),
    }

def normalize_loc_book(item: Dict[str, Any]) -> Dict[str, Any]:
    """تطبيع بيانات كتاب من Library of Congress."""
    return {
        "title": sanitize_string(item.get("title", "No Title")),
        "description": sanitize_string(item.get("description", ""))[:500],
        "thumbnail": sanitize_string(item.get("image_url", "")), # ✅ تم التعديل
        "source": "Library of Congress",
        "source_id": str(item.get("id", "")),
        "source_url": item.get("url", ""),
        "content_type": "book",
        "tags": _ensure_list(item.get("subject", [])),
        "language": "ar",
        "authors": _ensure_list(item.get("creator", [])),
    }

def normalize_archive_item(item: Dict[str, Any], content_type: str) -> Dict[str, Any]:
    """تطبيع بيانات من Internet Archive بناءً على نوع المحتوى."""
    description = item.get("description")
    if isinstance(description, list):
        description = description[0] if description else None

    identifier = item.get("identifier")
    source_url = f"https://archive.org/details/{identifier}" if identifier else None

    return {
        "title": sanitize_string(item.get("title", "No Title")),
        "description": sanitize_string(description)[:500] if description else "",
        "thumbnail": sanitize_string(f"https://archive.org/services/img/{identifier}" if identifier else ""), # ✅ تم التعديل
        "source": "Internet Archive",
        "source_id": str(identifier or ""),
        "source_url": source_url,
        "content_type": content_type,
        "tags": _ensure_list(item.get("subject", [])),
        "language": "ar",
        "authors": _ensure_list(item.get("creator", [])),
    }

def normalize_youtube_video(item: Dict[str, Any], content_type: str = "educational") -> Dict[str, Any]:
    """تطبيع بيانات فيديو من YouTube."""
    snippet = item.get("snippet", {})
    video_id = item.get("id", {}).get("videoId", "")
    return {
        "title": sanitize_string(snippet.get("title", "No Title")),
        "description": sanitize_string(snippet.get("description", ""))[:500],
        "thumbnail": sanitize_string(snippet.get("thumbnails", {}).get("high", {}).get("url", "")), # ✅ تم التعديل
        "source": "YouTube",
        "source_id": str(video_id or ""),
        "source_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
        "content_type": content_type,
        "tags": _ensure_list(snippet.get("tags", [])),
        "language": snippet.get("defaultAudioLanguage", "ar"),
        "authors": [sanitize_string(snippet.get("channelTitle", ""))],
    }
