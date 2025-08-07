import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def delete_text_index():
    client = AsyncIOMotorClient(settings.DB_URI)
    db = client[settings.DB_NAME]

    try:
        # التحقق من وجود الفهرس النصي
        indexes = await db.content.list_indexes().to_list()
        print(f"Current indexes for 'content' collection: {[idx['name'] for idx in indexes]}")

        # حذف الفهرس النصي إذا كان موجودًا
        if "text_index" in [idx["name"] for idx in indexes]:
            print("Dropping 'text_index' from 'content' collection...")
            await db.content.drop_index("text_index")
            print("Index 'text_index' dropped successfully.")
        else:
            print("'text_index' not found or already dropped.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(delete_text_index())
