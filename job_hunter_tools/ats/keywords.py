import json
import re
from pathlib import Path
from typing import Any


class SkillsDict:
    _instance: "SkillsDict | None" = None
    _data: dict[str, Any] | None = None

    def __new__(cls) -> "SkillsDict":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._data is not None:
            return
        data_path = Path(__file__).parent / "data" / "skills_dict.json"
        if data_path.exists():
            self._data = json.loads(data_path.read_text(encoding="utf-8"))
        else:
            self._data = {}

    @property
    def categories(self) -> list[str]:
        return [k for k in self._data if not k.startswith("_")]

    def all_skills(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for cat in self.categories:
            items = self._data[cat]
            if isinstance(items, dict):
                for skill_name, variants in items.items():
                    result[skill_name] = list(variants)
            elif isinstance(items, list):
                for skill_name in items:
                    result[skill_name] = [skill_name.lower()]
        return result

    def all_variants(self) -> dict[str, str]:
        variants: dict[str, str] = {}
        for skill_name, aliases in self.all_skills().items():
            normalized_name = skill_name.lower().strip()
            variants[normalized_name] = skill_name
            for alias in aliases:
                variants[alias.strip().lower()] = skill_name
        return variants

    def find_skills_in_text(self, text: str) -> dict[str, list[str]]:
        text_lower = text.lower()
        found: dict[str, list[str]] = {cat: [] for cat in self.categories}

        for cat in self.categories:
            items = self._data[cat]
            if not isinstance(items, dict):
                continue
            for skill_name, aliases in items.items():
                if self._skill_matches(skill_name, aliases, text_lower):
                    found[cat].append(skill_name)

        return {k: v for k, v in found.items() if v}

    def find_all_matches(self, text: str) -> set[str]:
        text_lower = text.lower()
        matched: set[str] = set()
        for skill_name, aliases in self.all_skills().items():
            if self._skill_matches(skill_name, aliases, text_lower):
                matched.add(skill_name)
        return matched

    def _skill_matches(self, skill_name: str, aliases: list[str], text_lower: str) -> bool:
        if _word_boundary_match(skill_name.lower(), text_lower):
            return True
        for alias in aliases:
            if _word_boundary_match(alias, text_lower):
                return True
        return False

    def extract_known_phrases(self, text: str, category: str | None = None) -> list[str]:
        text_lower = text.lower()
        found: list[str] = []
        cats = [category] if category else self.categories
        for cat in cats:
            items = self._data.get(cat, {})
            if not isinstance(items, dict):
                continue
            for skill_name in items:
                if self._skill_matches(skill_name, items[skill_name], text_lower):
                    found.append(skill_name)
        return found


def _word_boundary_match(phrase: str, text_lower: str) -> bool:
    escaped = re.escape(phrase)
    return bool(re.search(rf"(?<![a-zA-ZÀ-ÿ]){escaped}(?![a-zA-ZÀ-ÿ])", text_lower))
