from services.database import mongodb_service
from models.message import MessageCreate, MessageResponse
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class AsyncMessageService:
    async def create_message(self, message_data: MessageCreate) -> MessageResponse:
        """Create a new message"""
        try:
            collection = mongodb_service.get_collection("messages")

            # Prepare message document
            message_dict = message_data.dict()
            message_dict["timestamp"] = datetime.utcnow()

            result = await collection.insert_one(message_dict)

            # Return created message
            created_message = await collection.find_one({"_id": result.inserted_id})
            created_message["_id"] = str(created_message["_id"])
            # conversation_id is already stored as string, no conversion needed
            return MessageResponse(**created_message)

        except Exception as e:
            raise Exception(f"Failed to create message: {str(e)}")

    async def get_conversation_messages(
        self, conversation_id: str, page: int = 1, limit: int = 50
    ) -> List[MessageResponse]:
        """Get messages for a conversation with pagination"""
        try:
            collection = mongodb_service.get_collection("messages")

            skip = (page - 1) * limit
            cursor = (
                collection.find({"conversation_id": conversation_id})
                .sort("timestamp", 1)
                .skip(skip)
                .limit(limit)
            )

            messages = []
            async for message_doc in cursor:
                message_doc["_id"] = str(message_doc["_id"])
                # conversation_id is already stored as string, no conversion needed
                messages.append(MessageResponse(**message_doc))

            return messages

        except Exception as e:
            raise Exception(f"Failed to get conversation messages: {str(e)}")

    async def get_user_messages(
        self, user_id: str, page: int = 1, limit: int = 50
    ) -> List[MessageResponse]:
        """Get all messages for a user with pagination"""
        try:
            collection = mongodb_service.get_collection("messages")

            skip = (page - 1) * limit
            cursor = (
                collection.find({"user_id": user_id})
                .sort("timestamp", -1)
                .skip(skip)
                .limit(limit)
            )

            messages = []
            async for message_doc in cursor:
                message_doc["_id"] = str(message_doc["_id"])
                # conversation_id is already stored as string, no conversion needed
                messages.append(MessageResponse(**message_doc))

            return messages

        except Exception as e:
            raise Exception(f"Failed to get user messages: {str(e)}")


message_service = AsyncMessageService()
