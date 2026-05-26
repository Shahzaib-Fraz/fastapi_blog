from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models
import models
from schemes import UserPublic,UserPrivate, UserUpdate,UserCreate,PostResponse,Token
from config import settings

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from auth import hash_password, verify_password, create_access_token, Current_user

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result= await db.execute(select(models.User).where(func.lower(models.User.email)==func.lower(user.email)))
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Email already registered")
    

    result= await db.execute(select(models.User).where(func.lower(models.User.username)==func.lower(user.username)))
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    new_user=models.User(
        username=user.username,
        email=user.email.lower(),
        password_hash=hash_password(user.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    result= await db.execute(select(models.User).where(func.lower(models.User.email)==func.lower(form_data.username)))
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password")
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password")
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: Current_user):
    return current_user


@router.patch("/{user_id}",response_model=UserPrivate)
async def update_user(user_id:int, user_data: UserUpdate, current_user: Current_user, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    
    result= await db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_data.username and user_data.username.lower() != user.username.lower():
        result= await db.execute(select(models.User).where(func.lower(models.User.username)==func.lower(user_data.username)))
        existing_user=result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
    if user_data.email and user_data.email.lower() != user.email.lower():
        result= await  db.execute(select(models.User).where(func.lower(models.User.email)==func.lower(user_data.email)))
        existing_email=result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
    if user_data.username:
        user.username=user_data.username
    if user_data.email:
        user.email=user_data.email.lower()
    if user_data.image_file:
        user.image_file=user_data.image_file
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/{user_id}",response_model=UserPrivate)
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
async def delete_user(user_id: int, current_user: Current_user, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

    result=await db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    