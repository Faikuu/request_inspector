from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import timedelta
from database import get_db
from auth import create_access_token, verify_password, get_current_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from crud import get_resource_by_id, get_resource_by_uuid, verify_resource_password
from schemas import Token, ResourceCreate, TokenRequest
from models import Resource
import uuid

router = APIRouter()

@router.post("/token", response_model=Token)
async def generate_token(requested_resource: TokenRequest, db: AsyncSession = Depends(get_db)):
    resource = await verify_resource_password(db, requested_resource.resource_uuid, requested_resource.password, verify_password)
    if not resource:
        raise HTTPException(status_code=400, detail="Invalid resource ID or password")

    access_token = create_access_token(data={"sub": str(requested_resource.resource_uuid)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"uuid": resource.uuid, "access_token": access_token, "token_type": "bearer"}

@router.get("/{resource_uuid}")
async def get_resource(resource_uuid: str, token_resource_uuid: str = Depends(get_current_token), db: AsyncSession = Depends(get_db)):
    try:
        if str(resource_uuid) != token_resource_uuid:
            raise HTTPException(status_code=403, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    resource = await get_resource_by_uuid(db, resource_uuid)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return {"content": resource.uuid}

@router.post("/create", response_model=Token)
async def create_resource(resource: ResourceCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(resource.password)    
    tempUuid = str(uuid.uuid4())
    while await get_resource_by_uuid(db, tempUuid):
        tempUuid = str(uuid.uuid4())

    new_resource = Resource(uuid=tempUuid, password=hashed_password)
    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)
    access_token = create_access_token(data={"sub": str(new_resource.uuid)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"uuid": new_resource.uuid, "access_token": access_token, "token_type": "bearer"}
