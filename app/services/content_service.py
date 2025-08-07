# app/services/content_service.py
from beanie import PydanticObjectId
from typing import List, Optional

from app.db.models import BaseContent, Feedback, ContentCreateIn, ContentUpdateIn
from app.db.error_models import ContentNotFoundError

class ContentService:
    @staticmethod
    async def get_content_by_type(
        content_type: str,
        page: int,
        page_size: int,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[BaseContent]:
        """
        يجلب قائمة المحتوى مع دعم للبحث والفلترة والترقيم.
        """
        search_criteria = {"content_type": content_type, "deleted_at": None}
        
        if query:
            search_criteria["$text"] = {"$search": query}
        
        if tags:
            search_criteria["tags"] = {"$all": tags}
            
        content_list = await BaseContent.find(search_criteria)\
                                        .sort(-BaseContent.added_at)\
                                        .skip((page - 1) * page_size)\
                                        .limit(page_size)\
                                        .to_list()
        return content_list

    @staticmethod
    async def get_content_by_id(content_id: PydanticObjectId) -> BaseContent:
        """
        يجلب عنصر محتوى واحد بواسطة معرفه.
        """
        content = await BaseContent.find_one({"_id": content_id, "deleted_at": None})
        if not content:
            raise ContentNotFoundError(content_id=str(content_id))
        return content

    @staticmethod
    async def create_new_content(content_data: ContentCreateIn) -> BaseContent:
        """
        ينشئ عنصر محتوى جديد.
        """
        content = BaseContent(**content_data.dict())
        await content.insert()
        return content

    @staticmethod
    async def update_existing_content(content_id: PydanticObjectId, content_data: ContentUpdateIn) -> BaseContent:
        """
        يحدّث عنصر محتوى موجود.
        """
        content = await ContentService.get_content_by_id(content_id)
        update_data = content_data.dict(exclude_unset=True)
        await content.update({"$set": update_data})
        # يجب إعادة جلب المحتوى المحدث لضمان عرض البيانات الجديدة
        updated_content = await ContentService.get_content_by_id(content_id)
        return updated_content

    @staticmethod
    async def delete_content_by_id(content_id: PydanticObjectId):
        """
        يقوم بحذف ناعم لعنصر المحتوى.
        """
        content = await ContentService.get_content_by_id(content_id)
        await content.set({"deleted_at": datetime.utcnow()})
        return None # لا يوجد محتوى لإرجاعه بعد الحذف

    @staticmethod
    async def update_feedback_and_rating(feedback: Feedback):
        """
        يحدّث متوسط التقييم وعدد المقيمين بعد إضافة تقييم جديد.
        """
        content_id = feedback.content_id
        # استخدام aggregation pipeline للحصول على المتوسط والعدد بكفاءة
        pipeline = [
            {"$match": {"content_id": content_id}},
            {"$group": {
                "_id": "$content_id",
                "average_rating": {"$avg": "$rating"},
                "rating_count": {"$sum": 1}
            }}
        ]
        
        aggregation_result = await Feedback.aggregate(pipeline).to_list(1)
        
        if aggregation_result:
            stats = aggregation_result[0]
            await BaseContent.find_one({"_id": content_id}).update(
                {"$set": {
                    "average_rating": stats["average_rating"],
                    "rating_count": stats["rating_count"]
                }}
            )

