"""Grounded molecule chat; chemistry and angle evidence remain immutable."""

import json
from typing import Any
from app.core.config import settings
from app.schemas.chat_schema import ChatMessage, ChatResponse


def _facts(record: dict[str, Any], language: str) -> dict[str, Any]:
    suffix = "en" if language == "en" else "vi"
    return {key: record.get(key) for key in ("formula", "charge", "total_valence_electrons", "central_atom", "bonding_domains", "lone_pair_domains", "steric_number", "ax_en", "electron_geometry", "molecular_geometry", "ideal_angle")} | {"name": record[f"name_{suffix}"], "bond_angles": record.get("_bond_angles"), "polarity_note": record[f"polarity_note_{suffix}"], "teaching_note": record[f"teaching_note_{suffix}"]}


def _fallback_reply(record: dict[str, Any], language: str, reason: str | None) -> ChatResponse:
    bundle = record.get("_bond_angles") or {}
    preferred = (bundle.get("preferred") or [{}])[0].get("display_label")
    vsepr = (bundle.get("vsepr_prediction") or [{}])[0].get("display_label", record["ideal_angle"])
    if language == "en":
        text = f"The AI chat assistant is unavailable. For {record['formula']}, the molecule-specific angle is {preferred or 'unavailable'}; the general {record['ax_en']} VSEPR prediction is {vsepr}."
    else:
        text = f"Trợ lý AI hiện chưa sẵn sàng. Với {record['formula']}, góc riêng của phân tử là {preferred or 'chưa có'}; dự đoán VSEPR chung {record['ax_en']} là {vsepr}."
    return ChatResponse(reply=text, source="deterministic_fallback", fallback_reason=reason)


def generate_chat_reply(record: dict[str, Any], messages: list[ChatMessage], language: str = "vi") -> ChatResponse:
    if not (settings.ENABLE_CLAUDE and settings.ANTHROPIC_API_KEY):
        return _fallback_reply(record, language, "Claude is not configured.")
    try:
        from anthropic import Anthropic
        system = "Use only the immutable JSON facts. Never select, invent, average, or relabel bond angles. Reply briefly in " + ("English" if language == "en" else "Vietnamese") + ". Facts: " + json.dumps(_facts(record, language), ensure_ascii=False)
        response = Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=settings.PUBCHEM_TIMEOUT_SECONDS).messages.create(model=settings.ANTHROPIC_MODEL, max_tokens=700, temperature=0.3, system=system, messages=[{"role": item.role, "content": item.content} for item in messages])
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text").strip()
        return ChatResponse(reply=text, source="claude") if text else _fallback_reply(record, language, "The AI returned an empty response.")
    except Exception as exc:
        return _fallback_reply(record, language, type(exc).__name__)
