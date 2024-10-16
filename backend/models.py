from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String, unique=True, index=True)
    password = Column(String)
