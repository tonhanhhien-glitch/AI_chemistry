"""Claude may explain immutable facts; deterministic fallback is always available."""

import hashlib
import json
from typing import Any, Literal
from app.core.config import settings
from app.schemas.explanation_schema import ExplanationResponse, ExplanationSections
from app.services.validation_service import validate_explanation_text

_PROMPT_VERSION = "1.1"
_CACHE: dict[str, ExplanationResponse] = {}


def _angle_facts(record: dict[str, Any]) -> tuple[str | None, str]:
    bundle = record.get("_bond_angles") or {}
    preferred = bundle.get("preferred") or []
    vsepr = bundle.get("vsepr_prediction") or []
    return (preferred[0].get("display_label") if preferred else None, vsepr[0].get("display_label") if vsepr else record["ideal_angle"])


def _cache_key(record: dict[str, Any], language: str, level: str) -> str:
    facts = {key: record[key] for key in ("formula", "charge", "ax_en", "bonding_domains", "lone_pair_domains", "electron_geometry", "molecular_geometry", "ideal_angle")}
    facts["bond_angles"] = record.get("_bond_angles")
    raw = json.dumps([facts, language, level, _PROMPT_VERSION, settings.ANTHROPIC_MODEL], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def deterministic_explanation(record: dict[str, Any], level: str = "intermediate", language: str = "vi", reason: str | None = None) -> ExplanationResponse:
    preferred, vsepr = _angle_facts(record)
    if language == "en":
        sections = ExplanationSections(
            lewis=f"{record['formula']} has {record['total_valence_electrons']} valence electrons. The deterministic Lewis representation conserves every electron and has formal charges summing to {record['charge']}.",
            ax_en=f"The central atom has {record['bonding_domains']} bonding domains and {record['lone_pair_domains']} lone-pair domains, giving {record['ax_en']}.",
            electron_geometry=f"Its electron-domain geometry is {record['electron_geometry']}.",
            molecular_geometry=f"Its molecular geometry is {record['molecular_geometry']}. " + (f"Experimental or molecule-specific angle: {preferred}. " if preferred else "") + f"General {record['ax_en']} VSEPR prediction: {vsepr}.",
            structure_property=record["polarity_note_en"], learning_tip=record["teaching_note_en"],
            disclaimer="This prose only restates immutable evidence. Coordinate-derived, experimental, and general VSEPR angles are not interchangeable.",
        )
    else:
        sections = ExplanationSections(
            lewis=f"{record['formula']} có tổng {record['total_valence_electrons']} electron hoá trị. Biểu diễn Lewis tất định bảo toàn electron và tổng điện tích hình thức bằng {record['charge']}.",
            ax_en=f"Quanh nguyên tử trung tâm có {record['bonding_domains']} miền liên kết và {record['lone_pair_domains']} miền cặp electron tự do, nên ký hiệu là {record['ax_en']}.",
            electron_geometry=f"Hình học miền electron là {record['electron_geometry_vi']} ({record['electron_geometry']}).",
            molecular_geometry=f"Hình học phân tử là {record['molecular_geometry_vi']} ({record['molecular_geometry']}). " + (f"Góc thực nghiệm hoặc riêng của phân tử: {preferred}. " if preferred else "") + f"Dự đoán VSEPR chung {record['ax_en']}: {vsepr}.",
            structure_property=record["polarity_note_vi"], learning_tip=record["teaching_note_vi"],
            disclaimer="Phần chữ chỉ diễn giải bằng chứng bất biến; không đồng nhất góc thực nghiệm, góc từ tọa độ và dự đoán VSEPR chung.",
        )
    return ExplanationResponse(formula=record["formula"], level=level, language=language, sections=sections, source="deterministic_fallback", fallback_reason=reason, prompt_version=_PROMPT_VERSION)


def _call_claude(record: dict[str, Any], level: str, language: str, correction: str | None = None) -> ExplanationSections:
    from anthropic import Anthropic
    suffix = "en" if language == "en" else "vi"
    facts = {key: record[key] for key in ("formula", "charge", "total_valence_electrons", "bonding_domains", "lone_pair_domains", "ax_en", "electron_geometry", "molecular_geometry", "ideal_angle")}
    facts.update(bond_angles=record.get("_bond_angles"), polarity_note=record[f"polarity_note_{suffix}"], teaching_note=record[f"teaching_note_{suffix}"])
    system = "The supplied JSON facts and angle provenance are immutable. Never select, invent, average, or relabel an angle. Return JSON with exactly lewis, ax_en, electron_geometry, molecular_geometry, structure_property, learning_tip, disclaimer. Language: " + language + ". Level: " + level + "."
    if correction:
        system += " Previous output failed validation: " + correction
    response = Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=settings.PUBCHEM_TIMEOUT_SECONDS).messages.create(model=settings.ANTHROPIC_MODEL, max_tokens=1000, temperature=0, system=system, messages=[{"role": "user", "content": json.dumps(facts, ensure_ascii=False)}])
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return ExplanationSections.model_validate(json.loads(text))


def generate_explanation(record: dict[str, Any], level: Literal["basic", "intermediate", "advanced"] = "intermediate", language: Literal["vi", "en"] = "vi") -> ExplanationResponse:
    key = _cache_key(record, language, level)
    if key in _CACHE:
        return _CACHE[key]
    if not (settings.ENABLE_CLAUDE and settings.ANTHROPIC_API_KEY):
        result = deterministic_explanation(record, level, language, "Claude is not configured; using the deterministic explanation.")
        _CACHE[key] = result
        return result
    problems: list[str] = []
    for attempt in range(2):
        try:
            sections = _call_claude(record, level, language, ", ".join(problems) if attempt else None)
            valid, problems = validate_explanation_text(" ".join(sections.model_dump().values()), record)
            if valid:
                result = ExplanationResponse(formula=record["formula"], level=level, language=language, sections=sections, source="claude", prompt_version=_PROMPT_VERSION)
                _CACHE[key] = result
                return result
        except Exception as exc:
            problems = [type(exc).__name__]
            break
    result = deterministic_explanation(record, level, language, "The AI response was unavailable or contradictory; replaced with the deterministic template.")
    _CACHE[key] = result
    return result
