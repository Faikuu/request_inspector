from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Resource, ResourceLog

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user):
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_name(db: AsyncSession, name: str):
    result = await db.execute(select(User).filter(User.name == name))
    return result.scalar_one_or_none()

async def create_resource(db: AsyncSession, resource):
    new_resource = Resource(password=resource.password)
    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)
    return new_resource

async def get_resource_by_id(db: AsyncSession, resource_id: int):
    result = await db.execute(select(Resource).filter(Resource.id == resource_id))
    return result.scalar_one_or_none()

async def get_resource_by_uuid(db: AsyncSession, resource_uuid: int):
    result = await db.execute(select(Resource).filter(Resource.uuid == resource_uuid))
    return result.scalar_one_or_none()

async def verify_resource_password(db: AsyncSession, resource_uuid: str, password: str, verify_password_func):
    resource = await get_resource_by_uuid(db, resource_uuid)
    if not resource or not verify_password_func(password, resource.password):
        return None
    return resource

async def get_resource_history(db: AsyncSession, resource_id: int):
    result = await db.execute(select(ResourceLog).filter(ResourceLog.resource_id == resource_id).order_by(ResourceLog.timestamp.desc()))
    return result.scalars().all()
