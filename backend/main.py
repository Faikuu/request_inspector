from fastapi import FastAPI
from database import engine, Base 
from routes import user, resource

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(user.router, prefix="/users")
app.include_router(resource.router, prefix="/resources")

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI"}