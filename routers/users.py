from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models
import models
from schemes import UserResponse, UserUpdate,UserCreate,PostResponse

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result= await db.execute(select(models.User).where(models.User.email==user.email))
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Email already registered")
    

    result= await db.execute(select(models.User).where(models.User.username==user.username))
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    new_user=models.User(
        username=user.username,
        email=user.email
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.patch("/{user_id}",response_model=UserResponse)
async def update_user(user_id:int, user_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result= await db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_data.username and user_data.username != user.username:
        result= await db.execute(select(models.User).where(models.User.username==user_data.username))
        existing_user=result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
    if user_data.email and user_data.email != user.email:
        result= await  db.execute(select(models.User).where(models.User.email==user_data.email))
        existing_email=result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
    if user_data.username:
        user.username=user_data.username
    if user_data.email:
        user.email=user_data.email
    if user_data.image_file:
        user.image_file=user_data.image_file
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/{user_id}",response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get("/{user_id}/posts",response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result=await   db.execute(select(models.User).options(selectinload(models.User.posts)).where(models.User.id==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id==user_id))
    posts=result.scalars().all()
    return posts

@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    