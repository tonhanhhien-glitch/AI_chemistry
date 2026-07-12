"""Aggregate the currently implemented v1 API routes."""

from fastapi import APIRouter

from app.api.v1 import routes_formula, routes_health

api_router = APIRouter()
api_router.include_router(routes_health.router, tags=["health"])
api_router.include_router(routes_formula.router, tags=["formula"])
