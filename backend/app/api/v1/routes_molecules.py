"""Curated example and search endpoints."""

from fastapi import APIRouter, Query

from app.schemas.molecule_schema import MoleculeSearchResponse, MoleculeSummary
from app.services.molecule_resolver import list_examples, search_molecules

router = APIRouter()


@router.get("/molecules/examples", response_model=list[MoleculeSummary])
def get_examples() -> list[MoleculeSummary]:
    return list_examples()


@router.get("/molecules/search", response_model=MoleculeSearchResponse)
def get_search(q: str = Query(..., min_length=1, max_length=80)) -> MoleculeSearchResponse:
    return MoleculeSearchResponse(query=q, results=search_molecules(q))
