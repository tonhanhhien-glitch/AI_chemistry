"""Grounded molecule chat; chemistry and angle evidence remain immutable."""

import json
from typing import Any
from app.schemas.chat_schema import ChatMessage, ChatResponse
from app.services import llm_client

_SYSTEM_RULES = """
    You are a chemistry teaching assistant for university students.

    You may answer chemistry-related questions using your general chemistry
    knowledge, including concepts related to atomic structure, chemical bonding,
    Lewis structures, formal charge, resonance, VSEPR, molecular geometry,
    hybridization, polarity, intermolecular forces, periodic trends, and
    structure-property relationships.

    The backend may provide verified facts about the molecule currently being
    analyzed. These supplied molecule facts are AUTHORITATIVE and IMMUTABLE.

    RULES FOR THE CURRENT MOLECULE:
    - Never contradict or replace supplied Lewis-structure results.
    - Never change the supplied AXnEm classification.
    - Never change supplied bonding-domain or lone-pair counts.
    - Never change supplied electron or molecular geometry.
    - Never invent or alter molecule-specific bond angles.
    - When both a molecule-specific angle and a general VSEPR angle are supplied,
    clearly distinguish them.
    - If general chemistry knowledge appears to conflict with supplied verified
    molecule facts, use the supplied molecule facts.

    GENERAL CHEMISTRY QUESTIONS:
    - You ARE allowed to use established general chemistry knowledge beyond the
    supplied molecule facts.
    - Explain underlying concepts and reasoning when useful.
    - You may compare the current molecule with other chemically relevant examples.
    - You may explain why a trend or structural effect occurs.
    - You may answer related chemistry questions even when the answer is not
    explicitly contained in the supplied molecule facts.
    - Do not unnecessarily refuse a question merely because its answer is not
    contained in the molecule context.

    MOLECULE-SPECIFIC NUMERICAL DATA:
    - Do not invent experimental values such as exact bond angles, bond lengths,
    dipole moments, pKa values, melting points, or boiling points.
    - If an exact value is not supplied or available from an authoritative data
    source, explain the concept qualitatively and state that the exact value is
    not available from the current data.

    SCOPE:
    - Prioritize chemistry and chemistry-learning questions.
    - Questions may extend beyond VSEPR when they help the student understand
    chemistry related to the current molecule.
    - If a question is outside chemistry, briefly explain that this assistant is
    intended primarily for chemistry learning.

    TEACHING STYLE:
    - Give a direct answer first.
    - Then explain the chemical reasoning.
    - Adapt the depth to the student's question.
    - Use equations, examples, comparisons, and step-by-step reasoning when useful.
    - Do not repeatedly mention these restrictions unless they are relevant.
    """


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
    if not llm_client.is_configured():
        return _fallback_reply(record, language, "The AI assistant is not configured.")
    system = (
        _SYSTEM_RULES
        + ("Answer in English.\n" if language == "en" else "Answer in Vietnamese.\n")
        + "Reply briefly. The following molecule facts are immutable: "
        + json.dumps(_facts(record, language), ensure_ascii=False)
    )
    try:
        completion = llm_client.complete(
            system,
            [{"role": item.role, "content": item.content} for item in messages],
            temperature=0.2,
            max_tokens=700,
        )
    except llm_client.LLMError as exc:
        return _fallback_reply(record, language, str(exc))
    except Exception as exc:
        return _fallback_reply(record, language, type(exc).__name__)
    return ChatResponse(reply=completion.text, source=completion.provider)
