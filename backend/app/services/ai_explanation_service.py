"""Claude may explain immutable verified facts; deterministic fallback is always available."""

import hashlib
import json
from typing import Any, Literal

from app.core.config import settings
from app.schemas.explanation_schema import ExplanationResponse, ExplanationSections
from app.services.validation_service import validate_explanation_text

_PROMPT_VERSION = "1.0"
_CACHE: dict[str, ExplanationResponse] = {}


def _cache_key(record: dict[str, Any], language: str, level: str) -> str:
    facts = {key: record[key] for key in ("formula", "charge", "ax_en", "bonding_domains", "lone_pair_domains", "electron_geometry", "molecular_geometry", "ideal_angle")}
    raw = json.dumps([facts, language, level, _PROMPT_VERSION, settings.ANTHROPIC_MODEL], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def deterministic_explanation(record: dict[str, Any], level: str = "intermediate", language: str = "vi", reason: str | None = None) -> ExplanationResponse:
    if language == "en":
        sections = ExplanationSections(
            lewis=f"{record['formula']} has {record['total_valence_electrons']} valence electrons. The curated Lewis template conserves every electron and has formal charges summing to {record['charge']}.",
            ax_en=f"The central atom has {record['bonding_domains']} bonding domains and {record['lone_pair_domains']} lone-pair domains, giving {record['ax_en']}.",
            electron_geometry=f"Its electron-domain geometry is {record['electron_geometry']}.",
            molecular_geometry=f"Its molecular geometry is {record['molecular_geometry']}, with ideal angle(s) {record['ideal_angle']}.",
            structure_property=record["polarity_note_vi"], learning_tip="Count electron domains around the central atom; a multiple bond counts as one domain.",
            disclaimer="This explanation restates deterministic rule-engine facts. The 3D fallback is illustrative.",
        )
    else:
        sections = ExplanationSections(
            lewis=f"{record['formula']} có tổng {record['total_valence_electrons']} electron hoá trị. Mẫu Lewis đã tuyển chọn bảo toàn electron và tổng điện tích hình thức bằng {record['charge']}.",
            ax_en=f"Quanh nguyên tử trung tâm có {record['bonding_domains']} miền liên kết và {record['lone_pair_domains']} miền cặp electron tự do, nên ký hiệu là {record['ax_en']}.",
            electron_geometry=f"Hình học miền electron là {record['electron_geometry_vi']} ({record['electron_geometry']}).",
            molecular_geometry=f"Hình học phân tử là {record['molecular_geometry_vi']} ({record['molecular_geometry']}), với góc lý tưởng {record['ideal_angle']}.",
            structure_property=record["polarity_note_vi"], learning_tip=record["teaching_note_vi"],
            disclaimer="Nội dung này chỉ diễn giải dữ kiện bất biến từ bộ quy tắc. Mô hình 3D dự phòng chỉ có tính minh hoạ.",
        )
    return ExplanationResponse(formula=record["formula"], level=level, language=language, sections=sections, source="deterministic_fallback", fallback_reason=reason)


def _call_claude(record: dict[str, Any], level: str, language: str, correction: str | None = None) -> ExplanationSections:
    from anthropic import Anthropic  # optional dependency, imported only when used

    facts = {key: record[key] for key in ("formula", "charge", "total_valence_electrons", "bonding_domains", "lone_pair_domains", "ax_en", "electron_geometry", "molecular_geometry", "ideal_angle", "polarity_note_vi", "teaching_note_vi")}
    system = (
        "You are a chemistry teaching assistant. The supplied JSON facts are immutable. "
        "Never change Lewis structure, formal charge, domain counts, AXnEm, geometry, or angles. "
        "Return JSON with exactly: lewis, ax_en, electron_geometry, molecular_geometry, "
        "structure_property, learning_tip, disclaimer. Language: " + language + ". Level: " + level + "."
    )
    if correction:
        system += " Previous output failed validation: " + correction + ". Correct the prose without changing facts."
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=settings.PUBCHEM_TIMEOUT_SECONDS)
    response = client.messages.create(model=settings.ANTHROPIC_MODEL, max_tokens=1000, temperature=0, system=system, messages=[{"role": "user", "content": json.dumps(facts, ensure_ascii=False)}])
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return ExplanationSections.model_validate(json.loads(text))


def generate_explanation(record: dict[str, Any], level: Literal["basic", "intermediate", "advanced"] = "intermediate", language: Literal["vi", "en"] = "vi") -> ExplanationResponse:
    key = _cache_key(record, language, level)
    if key in _CACHE:
        return _CACHE[key]
    if not (settings.ENABLE_CLAUDE and settings.ANTHROPIC_API_KEY):
        result = deterministic_explanation(record, level, language, "Claude chưa được cấu hình; dùng bản giải thích xác định.")
        _CACHE[key] = result
        return result
    problems: list[str] = []
    for attempt in range(2):
        try:
            sections = _call_claude(record, level, language, ", ".join(problems) if attempt else None)
            combined = " ".join(sections.model_dump().values())
            valid, problems = validate_explanation_text(combined, record)
            if valid:
                result = ExplanationResponse(formula=record["formula"], level=level, language=language, sections=sections, source="claude")
                _CACHE[key] = result
                return result
        except Exception as exc:
            problems = [type(exc).__name__]
            break
    result = deterministic_explanation(record, level, language, "Phản hồi AI không khả dụng hoặc mâu thuẫn; đã thay bằng mẫu xác định.")
    _CACHE[key] = result
    return result
