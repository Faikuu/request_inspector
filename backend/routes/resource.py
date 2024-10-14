from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import timedelta
from database import get_db
from auth import create_access_token, verify_password, get_current_token, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from crud import get_resource_by_id, verify_resource_password
from schemas import Token, ResourceCreate
from models import Resource

router = APIRouter()

# Mocked database for resources (should be moved to actual DB)
resources_db = {}

@router.post("/token", response_model=Token)
async def generate_token(resource_id: int, password: str, db: AsyncSession = Depends(get_db)):
    resource = await verify_resource_password(db, resource_id, password, verify_password)
    if not resource:
        raise HTTPException(status_code=400, detail="Invalid resource ID or password")

    access_token = create_access_token(data={"sub": str(resource_id)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/{resource_id}")
async def get_resource(resource_id: int, token_resource_id: str = Depends(get_current_token), db: AsyncSession = Depends(get_db)):
    try:
        if str(resource_id) != token_resource_id:
            raise HTTPException(status_code=403, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    resource = await get_resource_by_id(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return {"content": resource.id}

@router.post("/create", response_model=Token)
async def create_resource(resource: ResourceCreate, db: AsyncSession = Depends(get_db)):
    new_resource = Resource(password=resource.password)
    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)
    access_token = create_access_token(data={"sub": str(new_resource.id)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}
