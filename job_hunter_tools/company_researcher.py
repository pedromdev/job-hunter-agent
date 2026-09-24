from __future__ import annotations

import json
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema


_TOOL_PARAMS = tool_parameters_schema(
    company_data=StringSchema(
        "JSON string with company research data. "
        "Fields:\n"
        "- name (str, required): Company name\n"
        "- description (str): What the company does\n"
        "- segment (str): Market segment/industry\n"
        "- website (str): Official website URL\n"
        "- leadership (list): List of {name, role, detail}\n"
        "- products (list): List of product/service names\n"
        "- clients (list): List of clients/partners\n"
        "- how_it_works (str): Business model, culture, operations\n"
        "- salary (list): List of {role, min, med, max, currency, source}\n"
        "- sources (list): List of source URLs",
    ),
    required=["company_data"],
)


@tool_parameters(_TOOL_PARAMS)
class CompanyResearcherTool(Tool):
    name = "company_researcher"
    description = (
        "Estrutura dados de pesquisa sobre uma empresa no formato padronizado. "
        "Recebe os dados brutos coletados pelo agente (via web_search + web_fetch), "
        "enriquece com busca salarial via web como fallback, "
        "e retorna um JSON com formatted_message (string pronta para exibição) "
        "e structured_data (dict completo). "
        "IMPORTANTE: O agente DEVE exibir o formatted_message exatamente como retornado, "
        "sem modificar, resumir ou reformatar."
    )

    @property
    def read_only(self) -> bool:
        return True

    async def execute(
        self,
        company_data: str,
        **kwargs: Any,
    ) -> str:
        data = self._parse(company_data)

        if not data.get("salary"):
            salary = await self._fetch_salary_enrichment(data["name"])
            if salary:
                data["salary"] = salary

        return json.dumps(
            {
                "formatted_message": self._build_message(data),
                "structured_data": data,
            },
            ensure_ascii=False,
            indent=2,
        )

    def _parse(self, raw: str) -> dict:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {"name": str(raw).strip()}
        data.setdefault("name", "")
        data.setdefault("description", "")
        data.setdefault("segment", "")
        data.setdefault("website", "")
        data.setdefault("leadership", [])
        data.setdefault("products", [])
        data.setdefault("clients", [])
        data.setdefault("how_it_works", "")
        data.setdefault("salary", [])
        data.setdefault("sources", [])
        return data

    async def _fetch_salary_enrichment(self, company: str) -> list:
        results = []
        encoded = re.sub(r"[^a-zA-Z0-9\s]", "", company).strip().replace(" ", "+")
        urls = [
            f"https://br.indeed.com/salaries/{encoded}-Salaries",
            f"https://www.glassdoor.com.br/Sal%C3%A1rios/{encoded}-sal%C3%A1rios-SRCH_IL.0,8_KE{len(encoded)},11.htm",
        ]
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            for url in urls:
                try:
                    resp = await client.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
                    )
                    if resp.status_code != 200:
                        continue
                    soup = BeautifulSoup(resp.text, "lxml")
                    text = soup.get_text(separator=" ", strip=True)
                    salaries = re.findall(
                        r"([A-Za-zÀ-ÿ\s/]+?)\s*(?:R\$\s*[\d\.,]+|US\$\s*[\d\.,]+|€\s*[\d\.,]+)",
                        text[:3000],
                    )
                    if salaries:
                        results.append({"source": url, "roles_found": list(set(salaries[:5]))})
                except Exception:
                    continue
        structured = []
        seen = set()
        for entry in results:
            src = entry.get("source", "web")
            for role in entry.get("roles_found", []):
                r = role.strip()
                if r and r not in seen:
                    seen.add(r)
                    structured.append({
                        "role": r,
                        "min": "-",
                        "med": "-",
                        "max": "-",
                        "currency": "R$",
                        "source": "Indeed/Glassdoor (não estruturado)",
                    })
        return structured

    def _build_message(self, data: dict) -> str:
        lines = []
        name = data["name"] or "Desconhecida"
        lines.append(f"🏢 EMPRESA: {name}")
        lines.append("━" * 30)
        lines.append("")

        if data.get("description"):
            lines.append("📋 Visão Geral")
            lines.append(data["description"])
            lines.append("")

        seg_website = []
        if data.get("segment"):
            seg_website.append(f"🏷️ Segmento: {data['segment']}")
        if data.get("website"):
            seg_website.append(f"🌐 Site: {data['website']}")
        if seg_website:
            lines.append(" | ".join(seg_website))
            lines.append("")

        if data.get("leadership"):
            lines.append("👤 Liderança")
            for person in data["leadership"]:
                line = f"• {person.get('name', '?')}"
                if person.get("role"):
                    line += f" — {person['role']}"
                if person.get("detail"):
                    line += f" ({person['detail']})"
                lines.append(line)
            lines.append("")

        if data.get("products"):
            lines.append("📦 Produtos/Serviços")
            for p in data["products"]:
                lines.append(f"• {p}")
            lines.append("")

        if data.get("clients"):
            lines.append("🤝 Clientes/Parceiros")
            for c in data["clients"]:
                lines.append(f"• {c}")
            lines.append("")

        if data.get("salary"):
            lines.append("💰 Faixa Salarial")
            lines.append(
                f"{'Cargo':<25} | {'Mínimo':<12} | {'Médio':<12} | {'Máximo':<12} | {'Fonte':<20}"
            )
            lines.append("─" * 85)
            for s in data["salary"]:
                role = s.get("role", "?")[:24]
                mi = str(s.get("min") or "-")[:11]
                me = str(s.get("med") or "-")[:11]
                ma = str(s.get("max") or "-")[:11]
                src = str(s.get("source") or "-")[:19]
                lines.append(f"{role:<25} | {mi:<12} | {me:<12} | {ma:<12} | {src:<20}")
            lines.append("")

        if data.get("how_it_works"):
            lines.append("📊 Como Atua")
            lines.append(data["how_it_works"])
            lines.append("")

        if data.get("sources"):
            joined = ", ".join(data["sources"][:5])
            lines.append(f"🔗 Fonte: {joined}")

        return "\n".join(lines)
