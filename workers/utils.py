# workers/utils.py
import re
import logging
from typing import Any, List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("worker_utils")

def sanitize_string(value: Any) -> str:
    """تنظيف وتنسيق السلاسل النصية"""
    if not value:
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
        "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
        "source": "Google Books",
        "source_id": str(item.get("id", "")),
        "source_url": info.get("infoLink", ""),
        "content_type": "book",
        "tags": _ensure_list(info.get("categories", [])),
        "language": info.get("language", "ar"), # ✅ إضافة اللغة
        "authors": _ensure_list(info.get("authors", [])), # ✅ إضافة المؤلفين
    }

def normalize_open_library_book(item: Dict[str, Any]) -> Dict[str, Any]:
    """تطبيع بيانات كتاب من Open Library."""
    cover_id = item.get('cover_i')
    return {
        "title": sanitize_string(item.get("title", "No Title")),
        "description": sanitize_string(item.get("first_sentence", [None])[0] if isinstance(item.get("first_sentence"), list) else item.get("first_sentence", ""))[:500],
        "thumbnail": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "",
        "source": "Open Library",
        "source_id": str(item.get("key", "").split("/")[-1] if item.get("key") else ""),
        "source_url": f"https://openlibrary.org{item.get('key', '')}",
        "content_type": "book",
        "tags": _ensure_list(item.get("subject", [])),
        "language": item.get("languages", [{}])[0].get("key", "").replace("/languages/", "") if item.get("languages") else "ar", # ✅ استخراج اللغة
        "authors": _ensure_list(item.get("author_name", [])), # ✅ إضافة المؤلفين
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
        "thumbnail": f"https://archive.org/services/img/{identifier}" if identifier else "",
        "source": "Internet Archive",
        "source_id": str(identifier or ""),
        "source_url": source_url,
        "content_type": content_type,
        "tags": _ensure_list(item.get("subject", [])),
        "language": "ar", # ✅ افتراضي للبحث بالعربية
        "authors": _ensure_list(item.get("creator", [])), # ✅ إضافة المؤلفين/الراوي
    }

def normalize_youtube_video(item: Dict[str, Any], content_type: str = "educational") -> Dict[str, Any]:
    """تطبيع بيانات فيديو من YouTube."""
    snippet = item.get("snippet", {})
    video_id = item.get("id", {}).get("videoId", "")
    return {
        "title": sanitize_string(snippet.get("title", "No Title")),
        "description": sanitize_string(snippet.get("description", ""))[:500],
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "source": "YouTube",
        "source_id": str(video_id or ""),
        "source_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
        "content_type": content_type,
        "tags": _ensure_list(snippet.get("tags", [])),
        "language": snippet.get("defaultAudioLanguage", "ar"), # ✅ استخراج اللغة
        "authors": [sanitize_string(snippet.get("channelTitle", ""))], # ✅ إضافة القناة كمؤلف
    }
