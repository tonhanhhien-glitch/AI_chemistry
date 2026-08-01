"""GET /health - reports backend status and version for uptime checks."""
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def get_health() -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
        "integrations": {
            "pubchem_enabled": settings.ENABLE_PUBCHEM,
            "rdkit_enabled": settings.ENABLE_RDKIT,
        },
    }
