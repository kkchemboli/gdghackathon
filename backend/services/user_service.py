from services.database import mongodb_service
from models.user import User, UserCreate
from pymongo.errors import DuplicateKeyError
from typing import Optional
from bson import ObjectId


class AsyncUserService:
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            collection = mongodb_service.get_collection("users")

            # Check if user already exists by email
            print(f"DEBUG: Searching for user with email: {user_data.email}")
            existing_user = await collection.find_one({"email": str(user_data.email)})
            print(existing_user)
            if existing_user is not None:
                print(f"DEBUG: Found existing user: {existing_user}")
                raise ValueError(f"User with email {user_data.email} already exists")

            # Insert new user - MongoDB will generate _id automatically
            user_dict = user_data.dict()
            result = await collection.insert_one(user_dict)

            # Return created user with string _id
            created_user = await collection.find_one({"_id": result.inserted_id})
            if created_user:
                created_user["_id"] = str(created_user["_id"])
                return User(**created_user)
            else:
                raise Exception("Failed to retrieve created user")

        except DuplicateKeyError as e:
            print(e)
            raise ValueError(f" Dup: User with email {user_data.email} already exists")
        except ValueError:
            raise   # 👈 do NOT wrap it
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")

    async def get_user(self, id: str) -> Optional[User]:
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
                user["_id"] = str(user["_id"])
                return User(**user)
            return None

        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            collection = mongodb_service.get_collection("users")
            user = await collection.find_one({"email": email})

            if user:
                user["_id"] = str(user["_id"])
                return User(**user)
            return None

        except Exception as e:
            raise Exception(f"Failed to get user by email: {str(e)}")


user_service = AsyncUserService()
