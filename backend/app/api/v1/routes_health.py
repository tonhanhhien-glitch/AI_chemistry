"""GET /health - reports backend status and version for uptime checks."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_health() -> dict:
    # TODO: read version from package metadata
    return {"status": "ok", "version": "0.1.0"}
