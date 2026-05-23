from datetime import datetime

from pydantic import BaseModel,Field,ConfigDict,EmailStr

class UserBase(BaseModel):
    username : str =Field(min_length=1, max_length=100)
    email : EmailStr =Field(max_length=120)
    # password : str =Field(min_length=1, max_length=100)

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=120)
    image_file: str | None = Field(default=None, max_length=200)
    # password: str | None = Field(default=None, min_length=1, max_length=100)

class UserResponse(UserBase):
    id: int
    image_path: str
    image_file: str | None
    model_config = ConfigDict(from_attributes=True)   # used to convert from dict to model, we can also use from_orm = True if we are using an ORM like SQLAlchemy


class PostBase(BaseModel):
    title : str =Field(min_length=1, max_length=100)
    content : str =Field(min_length=1)
    # author: str =Field(min_length=1, max_length=100)

class PostCreate(PostBase):
    user_id: int

class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)

    

class PostResponse(PostBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)   # used to convert from dict to model, we can also use from_orm = True if we are using an ORM like SQLAlchemy
    date_posted : datetime
    author: UserResponse
    