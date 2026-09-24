from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema

from .compass.archetypes import ARCHETYPES
from .compass.role_skills import ROLE_SKILLS

_TOOL_PARAMS = tool_parameters_schema(
    focus_skills=StringSchema(
        "JSON array de skills específicas que o usuário quer desenvolver. "
        "Ex: '[\"Kubernetes\", \"DDD\", \"CQRS\"]'. "
        "Se não fornecido, usa target_role. Se nenhum dos dois, usa ats_report.",
    ),
    target_role=StringSchema(
        "Cargo alvo para análise de skills necessárias. "
        "Ex: 'Tech Lead', 'Staff Engineer', 'Cloud Architect'. "
        "Ignorado se focus_skills for fornecido.",
    ),
    ats_report=StringSchema(
        "Texto completo do relatório ATS (retorno do ats_validator). "
        "A tool extrai automaticamente as skills ausentes. "
        "Ignorado se focus_skills ou target_role for fornecido.",
    ),
    resume_skills=StringSchema(
        "String com as skills do usuário separadas por vírgula ou espaço. "
        "Extraído da seção ## Habilidades do RESUME.md. "
        "Ex: 'Angular, TypeScript, Node.js, Docker'. "
        "Se não fornecido, a tool tenta ler o RESUME.md automaticamente.",
    ),
    user_context=StringSchema(
        "JSON opcional com contexto do usuário: "
        "{ 'constraints': '10h/semana', 'interests': ['backend', 'cloud'] }. "
        "Ajuda a priorizar projetos compatíveis.",
    ),
    required=[],
)

_SKILLS_DICT_PATH = Path(__file__).parent / "ats" / "data" / "skills_dict.json"


@tool_parameters(_TOOL_PARAMS)
class CareerCompassTool(Tool):
    name = "career_compass"
    description = (
        "Sugere projetos práticos para desenvolver skills específicas. "
        "Analisa gaps entre skills atuais e desejadas (por cargo, skills alvo, "
        "ou relatório ATS) e recomenda projetos do catálogo que melhor "
        "preenchem esses gaps. Ideal para planejamento de carreira."
    )

    @property
    def read_only(self) -> bool:
        return True

    async def execute(
        self,
        focus_skills: str | None = None,
        target_role: str | None = None,
        ats_report: str | None = None,
        resume_skills: str | None = None,
        user_context: str | None = None,
        **kwargs: Any,
    ) -> str:
        skills_dict = self._load_skills_dict()
        if not skills_dict:
            return "❌ Erro: não foi possível carregar o dicionário de skills (skills_dict.json)."

        lookup = self._build_skill_lookup(skills_dict)

        user_skills = self._resolve_user_skills(resume_skills, lookup)

        target_skills = self._resolve_target_skills(
            focus_skills, target_role, ats_report, lookup,
        )
        if not target_skills:
            return (
                "❌ Nenhuma skill alvo identificada. "
                "Forneça ao menos um dos parâmetros: focus_skills, target_role, ou ats_report."
            )

        gap_result = self._calculate_gaps(user_skills, target_skills)

        if not gap_result["gaps"]:
            return (
                "🎯 Você já domina todas as skills alvo! "
                "Tente um cargo mais desafiador ou skills mais específicas."
            )

        matches = self._match_projects(set(gap_result["gaps"]), user_skills)

        parsed_context = self._parse_user_context(user_context)

        return self._format_report(gap_result, matches, parsed_context)

    # ── Loaders ──────────────────────────────────────────────────────

    def _load_skills_dict(self) -> dict:
        path = _SKILLS_DICT_PATH
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        return text.lower().strip()

    def _build_skill_lookup(self, skills_dict: dict) -> dict[str, str]:
        lookup = {}
        for category, skills in skills_dict.items():
            if category == "_meta" or not isinstance(skills, dict):
                continue
            for canonical, variants in skills.items():
                norm = self._normalize(canonical)
                lookup[norm] = canonical
                for v in variants:
                    nv = self._normalize(v)
                    if nv not in lookup:
                        lookup[nv] = canonical
        return lookup

    # ── Skill resolution ─────────────────────────────────────────────

    def _resolve_user_skills(self, resume_skills: str | None, lookup: dict) -> set[str]:
        raw = resume_skills
        if not raw:
            raw = self._auto_read_resume_skills()
        if not raw:
            return set()
        return self._parse_skill_list(raw, lookup)

    def _parse_skill_list(self, text: str, lookup: dict) -> set[str]:
        skills = set()
        for part in re.split(r"[,\n;]+", text):
            part = part.strip().rstrip(".")
            if not part:
                continue
            norm = self._normalize(part)
            canonical = lookup.get(norm)
            skills.add(canonical or part)
        return skills

    def _auto_read_resume_skills(self) -> str:
        for candidate in (
            Path.cwd() / "RESUME.md",
            Path(__file__).parent.parent / "RESUME.md",
            Path.home() / ".nanobot" / "workspace" / "RESUME.md",
        ):
            if candidate.exists():
                content = candidate.read_text(encoding="utf-8")
                match = re.search(
                    r"## (?:Habilidades|Skills)\s*\n(.*?)(?=\n##\s|\Z)",
                    content,
                    re.DOTALL,
                )
                if match:
                    return match.group(1).strip()
        return ""

    def _resolve_target_skills(
        self,
        focus_skills: str | None,
        target_role: str | None,
        ats_report: str | None,
        lookup: dict,
    ) -> set[str]:
        if focus_skills:
            try:
                raw = json.loads(focus_skills)
                if isinstance(raw, list):
                    return self._parse_skill_list(", ".join(raw), lookup)
            except (json.JSONDecodeError, TypeError):
                pass

        if target_role:
            target_role = target_role.strip()
            if target_role in ROLE_SKILLS:
                return set(ROLE_SKILLS[target_role])
            norm_role = self._normalize(target_role)
            for role, skills in ROLE_SKILLS.items():
                if self._normalize(role) == norm_role:
                    return set(skills)
            return set()

        if ats_report:
            return self._parse_ats_gaps(ats_report, lookup)

        return set()

    def _parse_ats_gaps(self, report: str, lookup: dict) -> set[str]:
        skills = set()
        in_missing = False
        for line in report.split("\n"):
            stripped = line.strip()
            if "SKILLS AUSENTES" in stripped:
                in_missing = True
                continue
            if in_missing:
                if any(stripped.startswith(c) for c in ("🧠", "📊", "📄", "✅ NENHUMA", "💡", "━")):
                    break
                m = re.match(r"[•❌✅⚠️]\s+(.+?)(?:\s+\[.*?\]|\s+→|$)", stripped)
                if m:
                    skill = m.group(1).strip()
                    norm = self._normalize(skill)
                    canonical = lookup.get(norm, skill)
                    skills.add(canonical)
        return skills

    # ── Gap analysis ─────────────────────────────────────────────────

    @staticmethod
    def _calculate_gaps(user_skills: set[str], target_skills: set[str]) -> dict:
        matched = user_skills & target_skills
        gaps = target_skills - user_skills
        return {
            "matched": sorted(matched),
            "gaps": sorted(gaps),
            "total_target": len(target_skills),
            "total_user_in_target": len(matched),
            "total_gaps": len(gaps),
        }

    # ── Project matching ─────────────────────────────────────────────

    def _match_projects(self, gaps: set[str], user_skills: set[str]) -> list[dict]:
        norm_gaps = {self._normalize(g) for g in gaps}
        norm_user = {self._normalize(u) for u in user_skills}

        scored: list[dict] = []
        for proj in ARCHETYPES:
            proj_norm = {self._normalize(s) for s in proj.skills_developed}
            covered = proj_norm & norm_gaps
            if not covered:
                continue

            covered_originals = [
                g for g in gaps if self._normalize(g) in proj_norm
            ]
            new_skills = [
                s for s in proj.skills_developed
                if self._normalize(s) not in norm_user
            ]

            if len(gaps) > 0:
                coverage_score = len(covered) / len(gaps)
            else:
                coverage_score = 0
            focus_score = len(covered) / max(len(proj.skills_developed), 1)
            overall = coverage_score * 0.6 + focus_score * 0.4

            scored.append({
                "project": proj,
                "covered_gaps": covered_originals,
                "new_skills": new_skills,
                "score": round(overall, 3),
                "gap_coverage": f"{len(covered)}/{len(gaps)}",
            })

        scored.sort(key=lambda x: (-x["score"], -len(x["covered_gaps"])))
        return scored[:5]

    # ── Context ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_user_context(raw: str | None) -> dict:
        if not raw:
            return {}
        try:
            return json.loads(raw) if isinstance(raw, str) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    # ── Report formatting ────────────────────────────────────────────

    def _format_report(
        self,
        gap_result: dict,
        matches: list[dict],
        context: dict,
    ) -> str:
        lines: list[str] = []

        lines.append("🧭 CAREER COMPASS — Plano de Desenvolvimento")
        lines.append("━" * 52)
        lines.append("")

        lines.append("📊 ANÁLISE DE GAPS")
        lines.append(f"   Skills desejadas: {gap_result['total_target']}")
        lines.append(f"   Skills já domina: {gap_result['total_user_in_target']}")
        lines.append(f"   Gaps a preencher: {gap_result['total_gaps']}")
        if context.get("constraints"):
            lines.append(f"   ⏱ Disponibilidade: {context['constraints']}")
        lines.append("")

        if gap_result["matched"]:
            lines.append(f"✅ SKILLS DOMINADAS ({len(gap_result['matched'])})")
            for s in gap_result["matched"]:
                lines.append(f"   • {s}")
            lines.append("")

        if gap_result["gaps"]:
            lines.append(f"🎯 GAPS A DESENVOLVER ({len(gap_result['gaps'])})")
            for s in gap_result["gaps"]:
                lines.append(f"   • {s}")
            lines.append("")

        if not matches:
            lines.append("📌 Nenhum projeto do catálogo cobre os gaps atuais.")
            lines.append("   Tente skills mais específicas ou consulte o catálogo completo.")
            lines.append("")
        else:
            lines.append(f"📌 PROJETOS RECOMENDADOS")
            lines.append("")

            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, m in enumerate(matches):
                proj = m["project"]
                medal = medals[i] if i < len(medals) else "•"
                lines.append(f"{medal} {proj.name}")
                lines.append(f"   {'─' * 50}")
                lines.append(f"   Skills: {', '.join(proj.skills_developed)}")
                lines.append(
                    f"   Esforço: {proj.estimated_effort}  ·  "
                    f"Dificuldade: {proj.difficulty.title()}"
                )
                lines.append(f"   Stack: {', '.join(proj.tech_stack)}")
                lines.append("")
                lines.append(f"   {proj.description}")
                lines.append("")
                lines.append(
                    f"   ✅ Cobre: {', '.join(m['covered_gaps'])}"
                )
                if m["new_skills"]:
                    ns = m["new_skills"][:5]
                    lines.append(f"   🆕 Novas skills: {', '.join(ns)}")
                lines.append("")

        lines.append("━" * 52)
        lines.append(
            "💡 Priorize projetos que cobrem múltiplos gaps ou que usam "
            "tecnologias da sua stack para acelerar o aprendizado."
        )

        return "\n".join(lines)
