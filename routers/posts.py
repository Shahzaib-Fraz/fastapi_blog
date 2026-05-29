from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth import  Current_user
from fastapi import APIRouter, Depends, HTTPException, status,Query 
from sqlalchemy import select,func
from sqlalchemy.orm import selectinload
from schemes import PostCreate, PostResponse, PostUpdate, PaginatedPostsResponse
import models

router = APIRouter(prefix="/api/posts", tags=["posts"])

@router.get("/{post_id}",response_model=PostResponse)
async def get_post(post_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post

@router.put("/{post_id}",response_model=PostResponse)
async def update_full_post(post_id:int, post_data: PostCreate,current_user: Current_user,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.Post).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    post.title=post_data.title
    post.content=post_data.content
    
    await db.commit()
    await db.refresh(post, attribute_names=["author"])  # refresh the post to get the author relationship loaded, we can also use options(SelectinLoad(models.Post.author)) when querying the post to load the author relationship
    return post

@router.patch("/{post_id}",response_model=PostResponse)
async def update_post_partial(post_id:int, post_data: PostUpdate, current_user: Current_user, db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.Post).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found") 

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
 

    update_data=post_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    
    await db.commit()
    await db.refresh(post, attribute_names=["author"])  # refresh the post to get the author relationship loaded, we can also use options(SelectinLoad(models.Post.author)) when querying the post to load the author relationship
    return post





@router.post("",response_model=PostResponse,status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate,current_user: Current_user,db :Annotated[AsyncSession, Depends(get_db)]):
    

    new_post=models.Post(
        user_id=current_user.id,
        title=post.title,
        content=post.content
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post,attribute_names=["author"])  # refresh the post to get the author relationship loaded, we can also use options(SelectinLoad(models.Post.author)) when querying the post to load the author relationship
    return new_post

@router.get("",response_model=PaginatedPostsResponse)
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(1, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    count_result = await db.execute(select(func.count(models.Post.id)))
    total = count_result.scalar() or 0
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    has_more = skip + len(posts) < total
    

    return PaginatedPostsResponse(
        total=total,
        limit=limit,
        skip=skip,
        posts=[PostResponse.model_validate(post) for post in posts],
        has_more=has_more
    )


@router.delete("/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id:int,current_user: Current_user,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await  db.execute(select(models.Post).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")
    await db.delete(post)
    await db.commit()