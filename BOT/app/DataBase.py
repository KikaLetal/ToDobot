from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime

Base = declarative_base()
class Task(Base):
    __tablename__ = "Tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    status = Column(String, default='To Do 📝')

DATABASE_URL = "sqlite+aiosqlite:///Tasks.db"

engine = create_async_engine(DATABASE_URL)
AsyncSession = sessionmaker(bind = engine, class_=AsyncSession)

async def initDB():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

