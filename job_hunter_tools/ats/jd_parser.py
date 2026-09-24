from __future__ import annotations

import re
import unicodedata
from typing import Any

from .keywords import SkillsDict


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )

_REQUIRED_MARKERS_PT = [
    r"(?:^|\n)\s*requisitos?\b",
    r"(?:^|\n)\s*obrigat[oó]ri[oa]s?\b",
    r"(?:^|\n)\s*pr[ée]-requisitos?\b",
    r"(?:^|\n)\s*necess[áa]ri[oa]s?\b",
    r"(?:^|\n)\s*esperad[oa]s?\b",
    r"(?:^|\n)\s*buscamos\b",
    r"(?:^|\n)\s*procuramos\b",
    r"(?:^|\n)\s*exig[íi]mos\b",
]

_DESIRABLE_MARKERS_PT = [
    r"(?:^|\n)\s*diferenciais?\b",
    r"(?:^|\n)\s*desej[áa]vel\b",
    r"(?:^|\n)\s*ser[áa] um diferencial\b",
    r"(?:^|\n)\s*nice to have\b",
    r"(?:^|\n)\s*plus\b",
    r"(?:^|\n)\s*gostariamos\b",
    r"(?:^|\n)\s*valorizamos\b",
]

_REQUIRED_MARKERS_EN = [
    r"(?:^|\n)\s*requirements?\b",
    r"(?:^|\n)\s*required\b",
    r"(?:^|\n)\s*must have\b",
    r"(?:^|\n)\s*need\b",
    r"(?:^|\n)\s*we(?:'re| are) looking for\b",
    r"(?:^|\n)\s*essential\b",
]

_DESIRABLE_MARKERS_EN = [
    r"(?:^|\n)\s*nice to have\b",
    r"(?:^|\n)\s*preferred\b",
    r"(?:^|\n)\s*bonus points\b",
    r"(?:^|\n)\s*desirable\b",
    r"(?:^|\n)\s*plus\b",
    r"(?:^|\n)\s*it would be great if\b",
]


def classify_jd_skills(
    jd_text: str,
    skills_dict: SkillsDict | None = None,
    lang: str = "pt-br",
    required_headers_override: list[str] | None = None,
    desirable_headers_override: list[str] | None = None,
) -> dict[str, Any]:
    if skills_dict is None:
        skills_dict = SkillsDict()

    if required_headers_override is not None or desirable_headers_override is not None:
        return _classify_by_headers(
            jd_text, skills_dict,
            required_headers_override or [],
            desirable_headers_override or [],
        )

    required_markers = _REQUIRED_MARKERS_PT + _REQUIRED_MARKERS_EN
    desirable_markers = _DESIRABLE_MARKERS_PT + _DESIRABLE_MARKERS_EN

    all_skills_in_jd = skills_dict.find_all_matches(jd_text)
    sections = _split_sections(jd_text, required_markers + desirable_markers)

    required: set[str] = set()
    desirable: set[str] = set()

    for sec_title, sec_text in sections:
        title_lower = sec_title.lower()
        is_required = any(re.search(m, title_lower) for m in required_markers)
        is_desirable = any(re.search(m, title_lower) for m in desirable_markers)

        sec_skills = skills_dict.find_all_matches(sec_text)

        if is_required:
            required |= sec_skills
        elif is_desirable:
            desirable |= sec_skills

    unclassified = all_skills_in_jd - required - desirable

    required |= unclassified & _heuristic_required(
        jd_text, skills_dict, unclassified, lang
    )
    unclassified = all_skills_in_jd - required - desirable

    return {
        "required": sorted(required),
        "desirable": sorted(desirable),
        "unclassified": sorted(unclassified),
        "all": sorted(all_skills_in_jd),
        "method": "regex",
    }


def _classify_by_headers(
    jd_text: str,
    skills_dict: SkillsDict,
    required_headers: list[str],
    desirable_headers: list[str],
) -> dict[str, Any]:
    all_skills_in_jd = skills_dict.find_all_matches(jd_text)

    all_header_keywords = list(required_headers) + list(desirable_headers)
    sections = _parse_header_sections(jd_text, all_header_keywords)

    required: set[str] = set()
    desirable: set[str] = set()

    for sec_title, sec_text in sections:
        title_norm = _strip_accents(sec_title).lower()
        is_required = any(_strip_accents(h).lower() in title_norm for h in required_headers)
        is_desirable = any(_strip_accents(h).lower() in title_norm for h in desirable_headers)

        sec_skills = skills_dict.find_all_matches(sec_text)

        if is_required:
            required |= sec_skills
        elif is_desirable:
            desirable |= sec_skills

    unclassified = all_skills_in_jd - required - desirable

    return {
        "required": sorted(required),
        "desirable": sorted(desirable),
        "unclassified": sorted(unclassified),
        "all": sorted(all_skills_in_jd),
        "method": "agent_headers",
    }


def _parse_header_sections(
    jd_text: str,
    header_keywords: list[str],
) -> list[tuple[str, str]]:
    lines = jd_text.split("\n")
    header_positions: list[tuple[int, str]] = []

    keyword_normalized = [_strip_accents(k).lower() for k in header_keywords]

    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) > 80:
            continue
        prefix = stripped.split(":")[0].split(".")[0].strip()
        prefix_norm = _strip_accents(prefix).lower()
        for kw_norm in keyword_normalized:
            if kw_norm in prefix_norm:
                header_positions.append((i, stripped))
                break

    header_positions.sort(key=lambda x: x[0])

    if not header_positions:
        return [("", jd_text)]

    sections: list[tuple[str, str]] = []
    for idx, (start_line, title) in enumerate(header_positions):
        end_line = header_positions[idx + 1][0] if idx + 1 < len(header_positions) else len(lines)
        section_text = "\n".join(lines[start_line:end_line])
        sections.append((title, section_text))

    return sections


def _split_sections(text: str, markers: list[str]) -> list[tuple[str, str]]:
    pattern_parts = "|".join(f"({m})" for m in markers)
    pattern = re.compile(pattern_parts, re.IGNORECASE | re.MULTILINE)
    splits = list(pattern.finditer(text))

    if not splits:
        return [("", text)]

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(splits):
        title = match.group().strip()
        start = match.end()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
        sections.append((title, text[start:end].strip()))

    return sections


def _heuristic_required(
    jd_text: str,
    skills_dict: SkillsDict,
    unclassified: set[str],
    lang: str,
) -> set[str]:
    first_third = jd_text[: len(jd_text) // 3].lower()
    second_third = jd_text[len(jd_text) // 3 : 2 * len(jd_text) // 3].lower()

    likely_required: set[str] = set()
    for skill in unclassified:
        skill_lower = skill.lower()
        if skill_lower in first_third or skill_lower in second_third:
            likely_required.add(skill)
    return likely_required
