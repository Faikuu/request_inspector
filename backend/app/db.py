"""Async database engine, session factory and declarative base."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_engine(url: str, echo: bool = False) -> AsyncEngine:
    engine = create_async_engine(url, echo=echo, pool_pre_ping=True)
    if engine.sync_engine.dialect.name == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    from app import models  # noqa: F401  (registers the tables on Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session
