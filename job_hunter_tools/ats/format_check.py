from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .parser import extract_text

_OBSOLETE_SKILLS: dict[str, list[str]] = {
    "jquery": ["Substitua por React, Vue ou JavaScript vanilla moderno"],
    "angularjs": ["AngularJS (1.x) é legado. Use Angular 2+ ou migre para React/Vue"],
    "internet explorer": ["Tecnologia descontinuada. Substitua por menção a cross-browser compatível"],
    "gulp": ["Build tools modernas: Vite, Webpack, esbuild"],
    "grunt": ["Substitua por npm scripts, Webpack ou Vite"],
    "bower": ["Descontinuado. Use npm ou yarn para gerenciamento de pacotes"],
    "coffeescript": ["Linguagem em desuso. Prefira TypeScript ou JavaScript moderno (ES6+)"],
    "vbscript": ["Descontinuado. Use JavaScript ou TypeScript"],
    "flash": ["Tecnologia extinta em 2020. Remova do currículo"],
    "silverlight": ["Tecnologia extinta. Remova do currículo"],
    "cobol": ["Linguagem legada. A menos que a vaga peça explicitamente, evite destacar"],
    "delphi": ["Linguagem de nicho. Avalie se ainda é relevante para o mercado alvo"],
    "dreamweaver": ["Ferramenta obsoleta. Substitua por menção a IDEs modernas (VS Code, WebStorm)"],
    "ie6": ["Navegador extinto. Substitua por menção a compatibilidade cross-browser genérica"],
    "tableless": ["Termo técnico obsoleto. Já é padrão — não precisa destacar"],
    "mootools": ["Framework desaparecido. Remova do currículo"],
    "prototype.js": ["Framework desaparecido. Remova do currículo"],
    "sass": ["Ainda usado, mas prefira SCSS ou CSS Modules / CSS-in-JS para sinalizar modernidade"],
}

_PERSONAL_DATA_PATTERNS: dict[str, tuple[str, str, str]] = {
    "cpf": (r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "CPF detectado", "Nunca inclua CPF no currículo"),
    "rg": (r"\b\d{1,2}\.\d{3}\.\d{3}[-–]\d{1,2}\b", "RG detectado", "Nunca inclua RG no currículo"),
    "birth": (
        r"""(?ix)
        (?:data\s*(?:de\s*)?nascimento|nascido(?:\s*[ae])?[^\n]*?\d{2}[/-]\d{2}[/-]\d{2,4})
        |
        (\d{2}[/-]\d{2}[/-]\d{4})\s*[-–]\s*(?:data\s*(?:de\s*)?nascimento|nascimento)
        |
        idade\s*:\s*\d{2}
        """,
        "Data de nascimento ou idade detectada",
        "Remova data de nascimento e idade — podem gerar viés",
    ),
    "marital": (
        r"(?i)\b(solteiro|casado|divorciado|vi[úu]vo|uni[ãa]o\s+est[aá]vel|estado\s+civil)\b",
        "Estado civil detectado",
        "Estado civil é irrelevante para candidatura",
    ),
    "full_address": (
        r"""(?ix)
        (?:rua|avenida|av\.|travessa|alameda|praça|logradouro)
        \s+[\w\s]+\d+[\s,]*[-–]?\s*[\w\s]*,
        \s*\d{5}[-–]?\d{3}
        """,
        "Endereço completo detectado",
        "Informe apenas cidade/estado, nunca endereço completo",
    ),
    "nationality": (
        r"(?i)\b(nacionalidade|naturalidade|brasileiro|brasileira)\s*:\s*\w+",
        "Nacionalidade ou naturalidade detectada",
        "Nacionalidade não é necessária no currículo",
    ),
}


class ATSFormatCheck:
    def __init__(self, skills_dict: Any | None = None) -> None:
        self.skills_dict = skills_dict

    def check_personal_data(self, text: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for key, (pattern, title, suggestion) in _PERSONAL_DATA_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                preview = None
                for m in matches:
                    if isinstance(m, str) and m.strip():
                        preview = m.strip()
                        break
                    elif isinstance(m, tuple):
                        for g in m:
                            if g and g.strip():
                                preview = g.strip()
                                break
                    if preview:
                        break
                findings.append({
                    "type": key,
                    "severity": "error",
                    "title": title,
                    "preview": (preview or "")[:80],
                    "suggestion": suggestion,
                })
        return findings

    def check_section_objective(self, text: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        section_headers = [
            r"^objetivo\s*:?\s*$",
            r"^objective\s*:?\s*$",
            r"^objetivos?\s*(profissional(is)?)?\s*:?\s*$",
        ]
        text_lower = text.lower()
        for header in section_headers:
            if re.search(header, text_lower, re.MULTILINE):
                findings.append({
                    "type": "objective_section",
                    "severity": "warning",
                    "title": "Seção 'Objetivo' encontrada",
                    "preview": "",
                    "suggestion": "Substitua 'Objetivo' por um resumo profissional (about) "
                                  "adaptado à vaga + destaques com realizações",
                })
                break
        return findings

    def check_references_available(self, text: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        patterns = [
            r"(?i)refer[eê]ncias?\s*(dispon[ií]veis)?\s*(mediante\s*solicita[çc][ãa]o)?",
            r"(?i)references?\s*(available)?\s*(upon\s*request)?",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                findings.append({
                    "type": "references_section",
                    "severity": "warning",
                    "title": "'Referências disponíveis mediante solicitação' encontrado",
                    "preview": "",
                    "suggestion": "Remova — empregadores assumem que você pode fornecer "
                                  "referências quando solicitado",
                })
                break
        return findings

    def check_obsolete_skills(self, text: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        text_lower = text.lower()
        for obsolete_term, suggestions in _OBSOLETE_SKILLS.items():
            search_term = obsolete_term.lower().strip()
            if re.search(r"\b" + re.escape(search_term) + r"\b", text_lower):
                findings.append({
                    "type": "obsolete_skill",
                    "severity": "warning",
                    "title": f"Tecnologia desatualizada: {obsolete_term}",
                    "preview": obsolete_term,
                    "suggestion": suggestions[0] if suggestions else "Considere remover ou substituir",
                })
        return findings

    def check_bullet_ratio(self, text: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lines = text.split("\n")
        total_content_lines = 0
        bullet_lines = 0
        for line in lines:
            stripped = line.strip()
            if len(stripped) < 10:
                continue
            total_content_lines += 1
            if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("• "):
                bullet_lines += 1

        if total_content_lines > 0:
            ratio = bullet_lines / total_content_lines * 100
            if ratio < 20 and total_content_lines >= 10:
                findings.append({
                    "type": "low_bullet_ratio",
                    "severity": "info",
                    "title": "Baixo uso de bullet points",
                    "preview": f"{ratio:.0f}% dos {total_content_lines} parágrafos são bullets",
                    "suggestion": "Use mais bullet points (lista de tópicos) nas experiências "
                                  "em vez de parágrafos contínuos — ATS e recrutadores "
                                  "escaneam bullets primeiro",
                })
            return findings
        return findings

    def check_page_count(self, pdf_path: str, is_beginner: bool = False) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        if not os.path.exists(pdf_path):
            return findings
        ext = os.path.splitext(pdf_path)[1].lower()
        page_count = 0
        if ext == ".pdf":
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                page_count = len(reader.pages)
            except Exception:
                return findings
        else:
            return findings

        if is_beginner and page_count > 1:
            findings.append({
                "type": "too_many_pages",
                "severity": "warning",
                "title": "Currículo com mais de 1 página para iniciante",
                "preview": f"{page_count} páginas",
                "suggestion": "Para menos de 2 anos de experiência, prefira 1 página. "
                              "Seja mais seletivo nas experiências e projetos incluídos",
            })
        return findings

    def run_all(
        self,
        txt_path: str,
        pdf_path: str | None = None,
        is_beginner: bool = False,
    ) -> dict[str, Any]:
        if not os.path.exists(txt_path):
            return {"error": f"Arquivo não encontrado: {txt_path}", "checks": []}

        text = extract_text(txt_path)

        all_findings: list[dict[str, Any]] = []
        all_findings.extend(self.check_personal_data(text))
        all_findings.extend(self.check_section_objective(text))
        all_findings.extend(self.check_references_available(text))
        all_findings.extend(self.check_obsolete_skills(text))
        all_findings.extend(self.check_bullet_ratio(text))

        pdf_findings: list[dict[str, Any]] = []
        if pdf_path and os.path.exists(pdf_path):
            pdf_findings = self.check_page_count(pdf_path, is_beginner)
            all_findings.extend(pdf_findings)

        errors = [f for f in all_findings if f.get("severity") == "error"]
        warnings = [f for f in all_findings if f.get("severity") == "warning"]
        infos = [f for f in all_findings if f.get("severity") == "info"]

        has_issues = len(all_findings) > 0

        return {
            "has_issues": has_issues,
            "total_issues": len(all_findings),
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
            "checks": all_findings,
        }
