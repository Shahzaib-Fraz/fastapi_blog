from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


sqlalchemy_database_url="sqlite+aiosqlite:///./blog.db"

engine=create_async_engine(sqlalchemy_database_url,connect_args={"check_same_thread":False})

AsyncSessionLocal=async_sessionmaker(class_=AsyncSession, bind=engine,expire_on_commit=False)  # expire_on_commit=False is used to prevent the session from expiring after commit, which allows us to access the data after commit without having to refresh the session. This is useful in async context where we might want to access the data after commit without having to refresh the session.

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

