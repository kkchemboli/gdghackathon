from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr


class User(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True)

    id: str = Field(alias="_id")
    email: EmailStr
