"""Async SQLAlchemy Session Manager with PostGIS Geometry Compatibility via asyncpg

Manages connection pooling, lifecycle hooks, transaction boundaries, and spatial helpers.
"""

import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Tuple
from geoalchemy2 import WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.0 ORM models."""
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "application_name": "sts_fastapi_asyncpg",
        }
    },
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency Injection provider for isolated async database transactions.

    Yields an active AsyncSession, committing on successful endpoint execution
    and performing rollback on any raised exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for standalone scripts, background workers, and tasks."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def create_point_geography(
    longitude: float, latitude: float, srid: int = 4326
) -> WKTElement:
    """Creates a GeoAlchemy2 WKTElement for PostGIS GEOGRAPHY(POINT, 4326).

    Args:
        longitude: WGS84 Longitude in decimal degrees [-180.0, 180.0].
        latitude: WGS84 Latitude in decimal degrees [-90.0, 90.0].
        srid: Spatial Reference System Identifier (Default 4326).

    Returns:
        GeoAlchemy2 WKTElement formatted as 'SRID=4326;POINT(lon lat)'.
    """
    return WKTElement(f"SRID={srid};POINT({longitude} {latitude})", srid=srid)


def parse_geography_point(
    geometry_obj: Optional[object],
) -> Optional[Tuple[float, float]]:
    """Converts a PostGIS WKBElement, WKTElement, Shapely Point, or WKT string to a (longitude, latitude) tuple.

    Returns:
        Tuple of (longitude, latitude) or None.
    """
    if geometry_obj is None:
        return None

    try:
        if isinstance(geometry_obj, (WKBElement, WKTElement)):
            shapely_point: Point = to_shape(geometry_obj)
            return (shapely_point.x, shapely_point.y)
        if isinstance(geometry_obj, Point):
            return (geometry_obj.x, geometry_obj.y)
        if isinstance(geometry_obj, str):
            match = re.search(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", geometry_obj, re.IGNORECASE)
            if match:
                return (float(match.group(1)), float(match.group(2)))
    except Exception:
        pass
    return None
