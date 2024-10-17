from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

class ResourceCreate(BaseModel):
    password: str

class TokenRequest(BaseModel):
    resource_uuid: str
    password: str

class Resource(BaseModel):
    id: int
    uuid: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
