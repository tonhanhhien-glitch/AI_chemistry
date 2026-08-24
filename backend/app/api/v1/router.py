from fastapi import APIRouter

from backend.app.api.v1 import routes_formula, routes_health

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(routes_health.router, tags=["Health"])
api_router.include_router(routes_formula.router, tags=["Formula"])