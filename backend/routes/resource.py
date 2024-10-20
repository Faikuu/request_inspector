from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import timedelta
from database import get_db
from connection_manager import ConnectionManager
from auth import create_access_token, verify_password, get_current_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from crud import get_resource_by_id, get_resource_by_uuid, verify_resource_password, get_resource_history
from schemas import Token, ResourceCreate, TokenRequest, ResourceLogCreate
from models import Resource, ResourceLog
import uuid
import time

router = APIRouter()
manager = ConnectionManager()

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

@router.get("/history/{resource_uuid}")
async def get_resource(resource_uuid: str, token_resource_uuid: str = Depends(get_current_token), db: AsyncSession = Depends(get_db)):
    try:
        if str(resource_uuid) != token_resource_uuid:
            raise HTTPException(status_code=403, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    resource = await get_resource_by_uuid(db, resource_uuid)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    history = await get_resource_history(db, resource.id)
    if not history:
        raise HTTPException(status_code=404, detail="Resource history not found")

    return history

@router.post("/log")
async def log_to_resource(resource_log_create: ResourceLogCreate, token_resource_uuid: str = Depends(get_current_token), db: AsyncSession = Depends(get_db)):
    resource = await get_resource_by_uuid(db, token_resource_uuid)
    new_resource_log = ResourceLog(resource_id = resource.id, content = resource_log_create.content, timestamp = int(time.time()))
    db.add(new_resource_log)
    await db.commit()
    await db.refresh(new_resource_log)
    await manager.send_text(token_resource_uuid, resource_log_create.content)
    return {"content": "ok"}