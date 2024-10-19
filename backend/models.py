from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

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
    logs = relationship("ResourceLog", back_populates="resource")

class ResourceLog(Base):
    __tablename__ = 'resources_log'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey('resources.id'), index=True)
    content = Column(String)
    timestamp = Column(Integer, default=datetime.now().timestamp())
    resource = relationship("Resource", back_populates="logs")
