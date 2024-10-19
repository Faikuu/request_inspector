from fastapi import FastAPI, WebSocket
from database import engine, Base 
from routes import user, resource, ws
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(user.router, prefix="/users")
app.include_router(resource.router, prefix="/resources")
app.include_router(ws.router, prefix="/ws")

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI"}