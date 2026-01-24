from services.database import mongodb_service
from models.conversation import ConversationCreate, ConversationResponse
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class AsyncConversationService:
    async def create_conversation(
        self, conversation_data: ConversationCreate
    ) -> ConversationResponse:
        """Create a new conversation"""
        try:
            collection = mongodb_service.get_collection("conversations")

            # Prepare conversation document
            conversation_dict = conversation_data.dict()
            conversation_dict.update(
                {
                    "notes_url": None,
                    "concepts": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )

            result = await collection.insert_one(conversation_dict)

            # Return created conversation
            created_conversation = await collection.find_one(
                {"_id": result.inserted_id}
            )
            created_conversation["_id"] = str(created_conversation["_id"])
            return ConversationResponse(**created_conversation)

        except Exception as e:
            raise Exception(f"Failed to create conversation: {str(e)}")

    async def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationResponse]:
        """Get conversation by ID"""
        try:
            collection = mongodb_service.get_collection("conversations")
            conversation = await collection.find_one({"_id": ObjectId(conversation_id)})

            if conversation:
                conversation["_id"] = str(conversation["_id"])
                return ConversationResponse(**conversation)
            return None

        except Exception as e:
            raise Exception(f"Failed to get conversation: {str(e)}")

    async def find_by_video_url(
        self, user_id: str, video_url: str
    ) -> Optional[ConversationResponse]:
        """Find conversation by user_id and video_url"""
        try:
            collection = mongodb_service.get_collection("conversations")
            conversation = await collection.find_one(
                {"user_id": user_id, "video_url": video_url}
            )

            if conversation:
                conversation["_id"] = str(conversation["_id"])
                return ConversationResponse(**conversation)
            return None

        except Exception as e:
            raise Exception(f"Failed to find conversation by video URL: {str(e)}")

    async def get_user_conversations(self, user_id: str) -> List[ConversationResponse]:
        """Get all conversations for a user"""
        try:
            collection = mongodb_service.get_collection("conversations")
            cursor = collection.find({"user_id": user_id}).sort("created_at", -1)

            conversations = []
            async for conversation_doc in cursor:
                conversation_doc["_id"] = str(conversation_doc["_id"])
                conversations.append(ConversationResponse(**conversation_doc))

            return conversations

        except Exception as e:
            raise Exception(f"Failed to get user conversations: {str(e)}")

    async def update_conversation(
        self, conversation_id: str, notes_url: Optional[str] = None, concepts: Optional[List[str]] = None
    ) -> Optional[ConversationResponse]:
        """Update conversation with notes URL or concepts"""
        try:
            collection = mongodb_service.get_collection("conversations")

            update_fields = {"updated_at": datetime.utcnow()}
            if notes_url is not None:
                update_fields["notes_url"] = notes_url
            if concepts is not None:
                update_fields["concepts"] = concepts

            update_data = {"$set": update_fields}

            result = await collection.update_one(
                {"_id": ObjectId(conversation_id)}, update_data
            )

            if result.modified_count > 0 or result.matched_count > 0:
                return await self.get_conversation(conversation_id)
            return None

        except Exception as e:
            raise Exception(f"Failed to update conversation: {str(e)}")


conversation_service = AsyncConversationService()
