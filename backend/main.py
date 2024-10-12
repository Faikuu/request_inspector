from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from sqlalchemy.future import select

DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost/mydatabase"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

class UserCreate(BaseModel):
    name: str
    email: str

async def get_db():
    async with async_session() as session:
        yield session

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/users/create", response_model=UserCreate)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user) 
    return new_user

@app.post("/users/by-name/", response_model=UserCreate)
async def get_user_by_name(user: dict[str, str], db: AsyncSession = Depends(get_db)):
    query = select(User).filter(User.name == user.get('name'))
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    return existing_user

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI"}
