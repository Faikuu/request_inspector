from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

class ResourceCreate(BaseModel):
    password: str

class ResourceLogCreate(BaseModel):
    content: str

class TokenRequest(BaseModel):
    resource_uuid: str
    password: str

class Resource(BaseModel):
    id: int
    uuid: str
    password: str

class Token(BaseModel):
    uuid: str
    access_token: str
    token_type: str
