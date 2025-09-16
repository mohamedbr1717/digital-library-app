# app/db/static_data.py
from typing import Dict, Any

"""
هذا الملف يحتوي على البيانات الثابتة للكتب التعليمية.
فصل هذه البيانات يجعل الكود الرئيسي أكثر نظافة وسهولة في الصيانة.
"""

EDUCATIONAL_BOOKS_DATA: Dict[str, Dict[str, Any]] = {
    "arabic_primary": {
        "title": "📘 كتاب اللغة العربية - ابتدائي",
        "description": "أساسيات اللغة العربية للمرحلة الابتدائية.",
        "theme_class": "arabic-primary-theme",
        "sections": [
            {
                "title": "الوحدة 1: الحروف والكلمات",
                "items": [
                    {"icon": "📝", "text": "تمرين: كتابة الحروف الأبجدية", "link": "#"},
                    {"icon": "🎥", "text": "فيديو: تعلُّم الحروف بالصوت والصورة", "link": "#"},
                ]
            },
            {
                "title": "الوحدة 2: القراءة والفهم",
                "items": [
                    {"icon": "📝", "text": "تمرين: قراءة نصوص قصيرة", "link": "#"},
                    {"icon": "🎥", "text": "فيديو: قراءة قصص قصيرة", "link": "#"},
                ]
            }
        ]
    },
    "physics_middle": {
        "title": "📗 كتاب الفيزياء - إعدادي",
        "description": "مبادئ الفيزياء للمرحلة الإعدادية.",
        "theme_class": "physics-middle-theme",
        "sections": [
            {
                "title": "الوحدة 1: الحركة والقوى",
                "items": [
                    {"icon": "📝", "text": "تمرين: قوانين نيوتن", "link": "#"},
                    {"icon": "🎥", "text": "فيديو: تطبيقات على الحركة", "link": "#"},
                ]
            },
        ]
    },
    "math_middle": {
        "title": "📗 كتاب الرياضيات - إعدادي",
        "description": "أساسيات الجبر والهندسة للمرحلة الإعدادية.",
        "theme_class": "math-middle-theme",
        "sections": [
            {
                "title": "الوحدة 1: الجبر",
                "items": [
                    {"icon": "📝", "text": "تمرين: حل المعادلات البسيطة", "link": "#"},
                    {"icon": "🎥", "text": "فيديو: شرح المتغيرات", "link": "#"},
                ]
            },
        ]
    },
    # يمكنك إضافة باقي الكتب هنا بنفس الطريقة
}
