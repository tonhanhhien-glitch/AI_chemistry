"""Grounded molecule chat; chemistry and angle evidence remain immutable."""

import json
from typing import Any
from app.schemas.chat_schema import ChatMessage, ChatResponse
from app.services import openrouter_client

_SYSTEM_RULES = (
    "Answer only using the supplied molecule facts.\n"
    "Do not invent bond angles.\n"
    "Do not modify the AXnEm classification.\n"
    "Do not override the Lewis or VSEPR results.\n"
    "Clearly state when the supplied facts do not answer a question.\n"
)


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
    if not openrouter_client.is_configured():
        return _fallback_reply(record, language, "The AI assistant is not configured.")
    system = (
        _SYSTEM_RULES
        + ("Answer in English.\n" if language == "en" else "Answer in Vietnamese.\n")
        + "Reply briefly. The following molecule facts are immutable: "
        + json.dumps(_facts(record, language), ensure_ascii=False)
    )
    try:
        text = openrouter_client.complete(
            system,
            [{"role": item.role, "content": item.content} for item in messages],
            temperature=0.2,
            max_tokens=700,
        )
    except openrouter_client.OpenRouterError as exc:
        return _fallback_reply(record, language, str(exc))
    except Exception as exc:
        return _fallback_reply(record, language, type(exc).__name__)
    return ChatResponse(reply=text, source="openrouter")
