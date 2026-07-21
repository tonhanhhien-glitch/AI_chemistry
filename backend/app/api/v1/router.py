"""Aggregate the currently implemented v1 API routes."""

from fastapi import APIRouter

from app.api.v1 import (
    routes_analysis,
    routes_explanation,
    routes_feedback,
    routes_formula,
    routes_health,
    routes_molecules,
    routes_rules,
    routes_survey,
)

api_router = APIRouter()
api_router.include_router(routes_health.router, tags=["health"])
api_router.include_router(routes_formula.router, tags=["formula"])
api_router.include_router(routes_molecules.router, tags=["molecules"])
api_router.include_router(routes_analysis.router, tags=["analysis"])
api_router.include_router(routes_explanation.router, tags=["explanation"])
api_router.include_router(routes_rules.router, tags=["rules"])
api_router.include_router(routes_feedback.router, tags=["feedback"])
api_router.include_router(routes_survey.router, tags=["survey"])
