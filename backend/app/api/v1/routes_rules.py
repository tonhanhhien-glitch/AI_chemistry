"""Reviewable VSEPR rule and example endpoints."""

from fastapi import APIRouter

from app.chemistry.vsepr_rules import vsepr_rule_records
from app.schemas.molecule_schema import MoleculeSummary
from app.services.molecule_resolver import list_examples

router = APIRouter()


@router.get("/rules/vsepr")
def get_vsepr_rules() -> dict[str, object]:
    return {"schema_version": "1.0", "rules": vsepr_rule_records()}


@router.get("/rules/examples", response_model=list[MoleculeSummary])
def get_rule_examples() -> list[MoleculeSummary]:
    return list_examples()
