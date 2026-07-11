"""POST /analyze - runs the full parse -> resolve -> Lewis -> VSEPR -> 3D -> (AI explanation) pipeline."""
from fastapi import APIRouter

router = APIRouter()
