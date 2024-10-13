from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import UserCreate
from crud import create_user, get_user_by_name, get_user_by_email

router = APIRouter()

@router.post("/create", response_model=UserCreate)
async def create_user_route(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await create_user(db, user)
    return new_user

@router.post("/by-name/", response_model=UserCreate)
async def get_user_by_name_route(user: dict[str, str], db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_name(db, user.get('name'))
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    return existing_user