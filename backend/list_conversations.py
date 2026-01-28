
import asyncio
import os
from dotenv import load_dotenv
from services.database import mongodb_service
from services.conversation_service import conversation_service

async def main():
    load_dotenv()
    await mongodb_service.connect()
    
    print("Listing all conversations and concepts...")
    try:
        collection = mongodb_service.get_collection("conversations")
        cursor = collection.find({}).sort("created_at", -1)
        
        async for doc in cursor:
            print(f"ID: {doc.get('_id')}")
            print(f"Video: {doc.get('video_url')}")
            print(f"Concepts: {doc.get('concepts', [])}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await mongodb_service.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
