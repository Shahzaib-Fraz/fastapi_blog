from fastapi import APIRouter, Depends, HTTPException, status,UploadFile,Query,BackgroundTasks
from PIL import UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from image_utils import process_profile_picture,delete_profile_image
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from datetime import timedelta, datetime,UTC
from typing import Annotated
from sqlalchemy import select,delete as sql_delete
from sqlalchemy.orm import selectinload
import models
import models
from schemes import (ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, UserPublic,UserPrivate, 
                     UserUpdate,UserCreate,
                     PostResponse,Token,PaginatedPostsResponse,
)
from config import settings

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from auth import hash_password, verify_password, create_access_token, Current_user,generate_reset_token, hash_reset_token
from email_utils import send_password_reset_email

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

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Annotated[AsyncSession, Depends(get_db)]): 
    result= await db.execute(select(models.User).where(func.lower(models.User.email)==func.lower(request.email)))
    user=result.scalars().first()
    if user:
        result= await db.execute(sql_delete(models.PasswordResetToken).where(func.lower(models.PasswordResetToken.user_id)==func.lower(user.id)))
       
        token=generate_reset_token()
        hashed_token=hash_reset_token(token)
        expires_at=datetime.now(UTC)+timedelta(minutes=settings.password_reset_token_expire_minutes)

        reset_token=models.PasswordResetToken(
            user_id=user.id,
            token_hash=hashed_token,
            expires_at=expires_at
        )
        db.add(reset_token)
        
        await db.commit()
        background_tasks.add_task(send_password_reset_email,to_email=user.email,username=user.username, token=token)
    return {"message": "If an account with that email exists, a password reset link has been sent."}


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

@router.get("/{user_id}/posts",response_model=PaginatedPostsResponse)
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)],skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    result=await   db.execute(select(models.User).options(selectinload(models.User.posts)).where(models.User.id==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    count_result=await db.execute(select(func.count(models.Post.id)).where(models.Post.user_id==user_id))
    total=count_result.scalar() or 0
    
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id==user_id).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit))
    posts=result.scalars().all()
    return {"posts": posts, "total": total}

@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: Current_user, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

    result=await db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    old_filename=user.image_file
    await db.delete(user)
    await db.commit()
    if old_filename:
        delete_profile_image(old_filename)



@router.patch("/{user_id}/profile_picture",response_model=UserPrivate)
async def update_profile_picture(user_id: int, file: UploadFile, current_user: Current_user, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user's profile picture")
    
    content = await file.read()
    
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File size exceeds the maximum limit of {settings.max_upload_size_bytes // (1024 * 1024)} MB")
    try:
        new_filename= await run_in_threadpool(process_profile_picture, content)
    except UnidentifiedImageError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file") from err

    old_filename=current_user.image_file

    current_user.image_file=new_filename
    await db.commit()
    await db.refresh(current_user)
    if old_filename:
        delete_profile_image(old_filename)

    return current_user
    

@router.delete("/{user_id}/profile_picture",response_model=UserPrivate)
async def delete_profile_picture(user_id: int, current_user: Current_user, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user's profile picture")
    
    old_filename=current_user.image_file
    if not old_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No profile picture to delete")
    
    current_user.image_file=None
    await db.commit()
    await db.refresh(current_user)
    await delete_profile_image(old_filename)
    return current_user