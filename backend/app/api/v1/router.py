"""API v1 router with all endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import hcps
from app.api.v1.endpoints import interactions
from app.api.v1.endpoints import followups
from app.api.v1.endpoints import analytics
from app.api.v1.endpoints import ai
from app.api.v1.endpoints import support
from app.api.v1.endpoints import doctor
from app.api.v1.endpoints import audit
from app.api.v1.endpoints import search
from app.api.v1.endpoints import priorities

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(hcps.router, prefix="/hcps", tags=["HCPs"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["Interactions"])
api_router.include_router(followups.router, prefix="/followups", tags=["Follow-ups"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(support.router, prefix="/support", tags=["Support"])
# No prefix here - doctor.py's own routes already start with "/doctor"
# (e.g. "/doctor/me/profile", "/doctor/follow-ups").
api_router.include_router(doctor.router, tags=["Doctor"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(priorities.router, prefix="/priorities", tags=["Priorities"])