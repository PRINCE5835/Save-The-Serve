"""API v1 Router Aggregator

Aggregates all version 1 endpoints and namespaces for Save The Serve (S.T.S).
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, deliveries, donations, esg, ngos, settings, support

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    donations.router,
    prefix="/donations",
    tags=["Donations"],
)

api_router.include_router(
    deliveries.router,
    prefix="/deliveries",
    tags=["Deliveries"],
)

api_router.include_router(
    ngos.router,
    prefix="/ngos",
    tags=["NGOs"],
)

api_router.include_router(
    support.router,
    prefix="/support",
    tags=["Support"],
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["Settings"],
)

api_router.include_router(
    esg.router,
    prefix="/esg",
    tags=["ESG & Impact"],
)
