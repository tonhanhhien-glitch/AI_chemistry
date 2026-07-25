"""Claude answers learner questions grounded on a molecule's immutable facts.

The chemistry conclusions (Lewis structure, formal charge, electron/lone-pair
domain counts, AXnEm label, geometry, angles and polarity) come from the
deterministic rule engine and are supplied to the model as read-only context.
The system prompt forbids changing them. When Claude is not configured the
assistant returns a deterministic reply that points learners back to the
verified facts, so the pane stays useful offline.
"""

import json
from typing import Any

from app.core.config import settings
from app.schemas.chat_schema import ChatMessage, ChatResponse

_MAX_TOKENS = 700
_TEMPERATURE = 0.3


def _facts(record: dict[str, Any], language: str) -> dict[str, Any]:
    suffix = "en" if language == "en" else "vi"
    electron_geometry = (
        record["electron_geometry"]
        if language == "en"
        else f"{record['electron_geometry_vi']} ({record['electron_geometry']})"
    )
    molecular_geometry = (
        record["molecular_geometry"]
        if language == "en"
        else f"{record['molecular_geometry_vi']} ({record['molecular_geometry']})"
    )
    return {
        "formula": record["formula"],
        "name": record[f"name_{suffix}"],
        "charge": record["charge"],
        "total_valence_electrons": record["total_valence_electrons"],
        "central_atom": record["central_atom"],
        "bonding_domains": record["bonding_domains"],
        "lone_pair_domains": record["lone_pair_domains"],
        "steric_number": record["steric_number"],
        "ax_en": record["ax_en"],
        "electron_geometry": electron_geometry,
        "molecular_geometry": molecular_geometry,
        "ideal_angle": record["ideal_angle"],
        "pedagogical_hybridization": record.get("hybridization"),
        "polarity_note": record[f"polarity_note_{suffix}"],
        "teaching_note": record[f"teaching_note_{suffix}"],
    }


def _system_prompt(record: dict[str, Any], language: str) -> str:
    facts = json.dumps(_facts(record, language), ensure_ascii=False)
    reply_language = "English" if language == "en" else "Vietnamese"
    return (
        "You are a friendly chemistry tutor helping a student understand one specific "
        "molecule. The JSON facts below were produced by a deterministic rule engine and "
        "are the single source of truth. Never change or contradict the Lewis structure, "
        "formal charge, electron- or lone-pair domain counts, AXnEm label, electron or "
        "molecular geometry, bond angles, or polarity. If the student asks about something "
        "outside these facts or unrelated to this molecule, say briefly that you can only "
        "discuss this molecule's verified data, then steer back. Keep answers short "
        "(2-4 sentences), concrete, and suitable for a high-school or early-university "
        f"learner. Reply only in {reply_language}. Immutable facts: {facts}"
    )


def _fallback_reply(
    record: dict[str, Any], language: str, reason: str | None
) -> ChatResponse:
    if language == "en":
        text = (
            "The AI chat assistant is not available right now. You can still open the "
            "“Pedagogical explanation” section for a deterministic breakdown of "
            f"{record['formula']}: {record['ax_en']}, {record['molecular_geometry']} "
            f"geometry, ideal angle {record['ideal_angle']}."
        )
    else:
        text = (
            "Trợ lý hỏi đáp AI hiện chưa sẵn sàng. "
            "Bạn vẫn có thể mở phần “Giải thích "
            "sư phạm” để xem diễn giải xác định cho "
            f"{record['formula']}: {record['ax_en']}, hình học "
            f"{record['molecular_geometry_vi']}, góc lý tưởng "
            f"{record['ideal_angle']}."
        )
    return ChatResponse(reply=text, source="deterministic_fallback", fallback_reason=reason)


def generate_chat_reply(
    record: dict[str, Any], messages: list[ChatMessage], language: str = "vi"
) -> ChatResponse:
    if not (settings.ENABLE_CLAUDE and settings.ANTHROPIC_API_KEY):
        return _fallback_reply(record, language, "Claude is not configured.")
    try:
        from anthropic import Anthropic  # optional dependency, imported only when used

        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=settings.PUBCHEM_TIMEOUT_SECONDS)
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=_MAX_TOKENS,
            temperature=_TEMPERATURE,
            system=_system_prompt(record, language),
            messages=[{"role": message.role, "content": message.content} for message in messages],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text").strip()
    except Exception as exc:
        return _fallback_reply(record, language, type(exc).__name__)
    if not text:
        return _fallback_reply(record, language, "The AI returned an empty response.")
    return ChatResponse(reply=text, source="claude")
