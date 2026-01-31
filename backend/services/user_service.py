from pymongo.errors import DuplicateKeyError
from typing import Optional
from bson import ObjectId
from models.user import User, UserCreate, UserInDB
from services.database import mongodb_service


class UserService:
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        collection = mongodb_service.get_collection("users")
        user_data = await collection.find_one({"email": email})
        if user_data:
            return UserInDB(**user_data)
        return None

    async def get_or_create_user_from_google(self, google_user_info: dict) -> UserInDB:
        """
        Finds a user by email or creates a new one if they don't exist,
        using information from a verified Google ID token.
        """
        user_email = google_user_info.get("email")
        if not user_email:
            raise ValueError("Email not found in Google user info")

        existing_user = await self.get_user_by_email(user_email)
        if existing_user:
            # Optionally, update user's full_name and picture_url here if they've changed
            return existing_user

        # Create a new user if they don't exist
        new_user_data = UserCreate(
            email=user_email,
            full_name=google_user_info.get("name"),
            picture_url=google_user_info.get("picture"),
        )

        collection = mongodb_service.get_collection("users")
        user_dict = new_user_data.model_dump(by_alias=True)

        try:
            result = await collection.insert_one(user_dict)
        except DuplicateKeyError:
            # The user was created by another request between the find and insert calls.
            # We can now safely retrieve the user that was just created.
            existing_user = await self.get_user_by_email(user_email)
            if existing_user:
                return existing_user
            else:
                # This is a very unlikely scenario, but we should handle it.
                raise ValueError(
                    "Could not create or retrieve user after race condition."
                )

        created_user = await collection.find_one({"_id": result.inserted_id})
        if created_user:
            return UserInDB.model_validate(created_user)

        raise ValueError("Could not create user")

    async def get_user(self, id: str) -> Optional[UserInDB]:
        """Get user by MongoDB _id"""
        try:
            from bson.errors import InvalidId

            try:
                object_id = ObjectId(id)
            except InvalidId:
                return None

            collection = mongodb_service.get_collection("users")
            user = await collection.find_one({"_id": object_id})
            if user:
                return UserInDB(**user)
            return None
        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")


# Singleton instance of the user service
user_service = UserService()
