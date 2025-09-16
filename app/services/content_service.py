# app/services/content_service.py
from beanie import PydanticObjectId
from typing import List, Optional
from datetime import datetime
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
        content = await BaseContent.find_one({"_id": content_id, "deleted_at": None})
        if not content:
            raise ContentNotFoundError(content_id=str(content_id))
        return content

    @staticmethod
    async def create_new_content(content_data: ContentCreateIn) -> BaseContent:
        content = BaseContent(**content_data.dict())
        await content.insert()
        return content

    @staticmethod
    async def update_existing_content(content_id: PydanticObjectId, content_data: ContentUpdateIn) -> BaseContent:
        content = await ContentService.get_content_by_id(content_id)
        update_data = content_data.dict(exclude_unset=True)
        await content.set(update_data)
        updated_content = await ContentService.get_content_by_id(content_id)
        return updated_content

    @staticmethod
    async def delete_content_by_id(content_id: PydanticObjectId):
        content = await ContentService.get_content_by_id(content_id)
        # ✅ استخدام الحذف الناعم
        await content.set({"deleted_at": datetime.utcnow()})
        return None

    @staticmethod
    async def update_feedback_and_rating(feedback: Feedback):
        content_id = feedback.content_id
        # ✅ استخدام aggregation pipeline للحصول على المتوسط والعدد بكفاءة
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

    @staticmethod
    async def get_feedback_for_content(content_id: PydanticObjectId):
        feedbacks = await Feedback.find(Feedback.content_id == content_id).sort(-Feedback.created_at).to_list()
        return feedbacks
