from pydantic import BaseModel,Field,ConfigDict

class PostBase(BaseModel):
    title : str =Field(min_length=1, max_length=100)
    content : str =Field(min_length=1)
    author: str =Field(min_length=1, max_length=100)

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int

    model_config = ConfigDict(from_attributes=True)   # used to convert from dict to model, we can also use from_orm = True if we are using an ORM like SQLAlchemy
    date_posted : str