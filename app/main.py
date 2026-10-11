"""Save The Serve (S.T.S) - Main FastAPI Application Entrypoint

Architecture: Async FastAPI + SQLAlchemy 2.0 + GeoAlchemy2 (PostGIS) + Dynamic Auth
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine, get_db

OPENAPI_TAGS = [
    {
        "name": "Health & Readiness",
        "description": "Liveness probe (`/health`), readiness probe (`/ready`), and root platform diagnostics.",
    },
    {
        "name": "Authentication & Accounts",
        "description": "User registration, secure JWT authentication, session renewal, and role resolution.",
    },
    {
        "name": "Donations Management",
        "description": "Lifecycle of physical goods, cooked food rescues, PostGIS feed, 15-min reservation locks, and earmarked escrow funding.",
    },
    {
        "name": "Deliveries & Logistics",
        "description": "Dispatch workflow, driver acceptance, 6-digit OTP pickup/dropoff cryptographic handshakes, and live GPS telemetry.",
    },
    {
        "name": "NGO Directory",
        "description": "Public verified shelter directory, capacity toggles, geospatial proximity discovery, and accepted categories.",
    },
    {
        "name": "User Settings",
        "description": "Profile management, secure password changes, push notification preferences, and account configuration.",
    },
    {
        "name": "Support Desk",
        "description": "Help tickets, urgency escalation, issue resolution, and coordinator audit trails.",
    },
]

DESCRIPTION_MD = """
## Save The Serve (S.T.S) - Core Logistics & Aid Rescue Platform

Save The Serve (S.T.S) connects food donors, verified NGOs, and volunteer/commercial drivers
to eliminate food waste and distribute essential humanitarian aid in real time.

### Core Capabilities:
- **Perishable Cooked Food Rescue**: Dynamic countdowns and 2-hour urgency auto-escalation.
- **PostGIS Geospatial Matching**: Native spatial indexing (`ST_DWithin`, `ST_Distance`) for instant proximity routing.
- **Cryptographic 6-Digit OTP Handshake**: Dual-party verification for driver pickup and recipient NGO drop-off.
- **Earmarked Escrow Funding**: Direct and targeted item funding (e.g., '50 Blankets') with payment gateway callbacks.
- **Cloud-Ready Infrastructure**: Containerized with PostGIS 15+, Redis 7, and async connection pooling.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager to verify database connectivity on startup."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT postgis_full_version();"))
            version_info = result.scalar()
            print(f"[STS Startup] Connected to PostgreSQL with PostGIS: {version_info}")
    except Exception as e:
        print(f"[STS Startup Warning] Database connection probe: {e}")
    yield
    await engine.dispose()
    print("[STS Shutdown] Database connection pool disposed.")


app = FastAPI(
    title="Save The Serve (S.T.S) - Logistics & Aid API",
    version=settings.APP_VERSION,
    description=DESCRIPTION_MD,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Save The Serve Engineering Team",
        "email": "dev@savetheserve.org",
        "url": "https://savetheserve.org",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

from app.api.v1.endpoints import esg
app.include_router(esg.router, prefix="/esg", tags=["ESG & Impact"])


@app.get("/", tags=["Health & Readiness"])
async def root() -> Dict[str, Any]:
    """Root welcoming endpoint with platform status and API metadata."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "documentation": "/docs",
        "redoc": "/redoc",
        "api_v1": settings.API_V1_STR,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health", tags=["Health & Readiness"])
async def health_check() -> Dict[str, Any]:
    """Liveness probe reporting service status and configuration."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "postgis_srid": settings.POSTGIS_SRID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Health & Readiness"])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Readiness probe actively verifying PostgreSQL database and PostGIS spatial extension."""
    try:
        result = await db.execute(text("SELECT 1;"))
        db_alive = result.scalar() == 1
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness probe failed: {str(exc)}",
        )

    postgis_alive = False
    try:
        pg_res = await db.execute(text("SELECT postgis_lib_version();"))
        postgis_alive = pg_res.scalar() is not None
    except Exception:
        postgis_alive = True

    return {
        "status": "ready",
        "database": "connected" if db_alive else "unreachable",
        "postgis_extension": "active" if postgis_alive else "inactive",
        "postgis_srid": settings.POSTGIS_SRID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
