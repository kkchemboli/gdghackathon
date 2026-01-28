from pymongo import ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticDatabase, AgnosticCollection
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class AsyncMongoDBService:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AgnosticDatabase] = None
        self.connection_string = os.getenv("MONGODB_CONNECTION_STRING")

    async def connect(self):
        """Connect to MongoDB using AsyncIOMotorClient"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            # Test connection
            await self.client.admin.command("ping")
            self.db = self.client.default
            print("Connected to MongoDB successfully")
            return self.client
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    async def create_indexes(self):
        """Create necessary indexes for performance"""
        if self.db is None:
            raise RuntimeError("Database not connected")

        try:
            # Users collection indexes
            users_collection = self.db.users
            await users_collection.create_index("email", unique=True)
            print("Created unique index on user email.")

            # Conversations collection indexes
            conversations_collection = self.db.conversations
            await conversations_collection.create_index("user_id")

            # Add composite index for efficient (user_id, video_url) lookups
            try:
                await conversations_collection.create_index(
                    [("user_id", ASCENDING), ("video_url", ASCENDING)]
                )
                print("Created composite index on (user_id, video_url)")
            except Exception as e:
                # Graceful handling if index already exists or creation fails
                print(
                    f"Warning: Failed to create composite index (user_id, video_url): {e}"
                )
                print("Continuing without composite index - URL lookups may be slower")

            # Messages collection indexes
            messages_collection = self.db.messages
            await messages_collection.create_index("conversation_id")
            await messages_collection.create_index(
                [("user_id", ASCENDING), ("timestamp", -1)]
            )

            print("Database indexes created successfully")
        except Exception as e:
            print(f"Failed to create indexes: {e}")
            raise

    def get_collection(self, name: str) -> AgnosticCollection:
        """Get async collection"""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[name]


# Global instance
mongodb_service = AsyncMongoDBService()
