from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema

PLATFORMS_FILE = Path(
    os.environ.get("JOB_HUNTER_PLATFORMS_FILE", str(Path.home() / ".nanobot" / "workspace" / "JOBS_PLATFORMS.md"))
)

PLATFORM_HANDLERS: dict[str, dict[str, Any]] = {
    "indeed": {
        "name": "Indeed",
        "search_url": "https://www.indeed.com/rss?q={query}&l={location}",
        "parse": "rss",
    },
    "indeed_br": {
        "name": "Indeed Brasil",
        "search_url": "https://br.indeed.com/rss?q={query}&l={location}",
        "parse": "rss",
    },
    "remoteok": {
        "name": "Remote OK",
        "search_url": "https://remoteok.com/api?query={query}",
        "parse": "json",
    },
    "programathor": {
        "name": "Programathor",
        "search_url": "https://programathor.com.br/jobs?search={query}",
        "parse": "html",
    },
    "geekhunter": {
        "name": "GeekHunter",
        "search_url": "https://www.geekhunter.com.br/vagas?search={query}",
        "parse": "html",
    },
}

_TOOL_PARAMS = tool_parameters_schema(
    query=StringSchema("Search query, e.g. 'Python developer' or 'Engenheiro de dados'"),
    location=StringSchema("Optional location filter, e.g. 'Remote' or 'São Paulo'"),
    platforms=StringSchema(
        "Comma-separated platform keys to search (e.g. 'indeed,remoteok'). "
        "If empty, searches all configured platforms.",
    ),
    required=["query"],
)


@tool_parameters(_TOOL_PARAMS)
class JobScraperTool(Tool):
    name = "job_scraper"
    description = (
        "Search for job listings across configured platforms. "
        "Reads JOBS_PLATFORMS.md for available platform keys. "
        "Returns structured job listings with title, company, location, description, and URL."
    )

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, query: str, location: str = "", platforms: str = "", **kwargs: Any) -> str:
        platform_keys = [p.strip() for p in platforms.split(",") if p.strip()] if platforms else []

        results: list[dict[str, str]] = []
        errors: list[str] = []

        targets = self._resolve_targets(platform_keys)

        for key, config in targets.items():
            try:
                url = config["search_url"].format(
                    query=quote_plus(query),
                    location=quote_plus(location) if location else "",
                )
                jobs = await self._fetch_and_parse(url, config["parse"], key)
                results.extend(jobs)
            except Exception as e:
                errors.append(f"{config['name']}: {str(e)}")

        if not results and not errors:
            return "Nenhuma vaga encontrada. Tente um termo de busca diferente ou use web_search para explorar mais plataformas."

        parts: list[str] = []
        if results:
            parts.append(f"## Vagas encontradas ({len(results)})\n")
            for job in results:
                parts.append(f"### {job.get('title', 'Sem título')}")
                parts.append(f"**Empresa:** {job.get('company', 'N/A')}")
                parts.append(f"**Local:** {job.get('location', 'N/A')}")
                parts.append(f"**Plataforma:** {job.get('platform', 'N/A')}")
                desc = job.get("description", "")
                if desc:
                    parts.append(f"**Descrição:** {desc[:300]}{'...' if len(desc) > 300 else ''}")
                parts.append(f"**Link:** {job.get('url', '#')}")
                parts.append("")

        if errors:
            parts.append(f"## Erros ({len(errors)})\n")
            for err in errors:
                parts.append(f"- {err}")

        return "\n".join(parts)

    def _resolve_targets(self, platform_keys: list[str]) -> dict[str, dict[str, Any]]:
        if platform_keys:
            return {k: v for k, v in PLATFORM_HANDLERS.items() if k in platform_keys}
        enabled = self._read_platforms_file()
        if enabled:
            return {k: v for k, v in PLATFORM_HANDLERS.items() if k in enabled}
        return dict(PLATFORM_HANDLERS)

    def _read_platforms_file(self) -> list[str]:
        try:
            text = PLATFORMS_FILE.read_text()
            enabled = re.findall(r"^##\s+(\w+)", text, re.MULTILINE)
            return [p.lower() for p in enabled]
        except FileNotFoundError:
            return []
        except Exception:
            return []

    async def _fetch_and_parse(self, url: str, parse_mode: str, platform_key: str) -> list[dict[str, str]]:
        if parse_mode == "rss":
            return await self._parse_rss(url, platform_key)
        elif parse_mode == "json":
            return await self._parse_json(url, platform_key)
        elif parse_mode == "html":
            return await self._parse_html(url, platform_key)
        return []

    async def _fetch_text(self, url: str) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            return resp.text

    async def _parse_rss(self, url: str, platform_key: str) -> list[dict[str, str]]:
        text = await self._fetch_text(url)
        soup = BeautifulSoup(text, "lxml-xml")
        items = soup.find_all("item")
        results = []
        for item in items:
            title = item.find("title")
            company_tag = item.find("company") or item.find("author")
            desc = item.find("description")
            link = item.find("link")
            results.append({
                "title": title.text.strip() if title else "N/A",
                "company": company_tag.text.strip() if company_tag else "N/A",
                "description": BeautifulSoup(desc.text if desc else "", "html.parser").get_text().strip()
                if desc else "",
                "url": link.text.strip() if link else "#",
                "location": "",
                "platform": PLATFORM_HANDLERS.get(platform_key, {}).get("name", platform_key),
            })
        return results

    async def _parse_json(self, url: str, platform_key: str) -> list[dict[str, str]]:
        text = await self._fetch_text(url)
        data = json.loads(text)
        results = []
        items = data if isinstance(data, list) else data.get("jobs", data.get("data", []))
        for item in items:
            results.append({
                "title": item.get("title", item.get("position", "N/A")),
                "company": item.get("company", item.get("company_name", "N/A")),
                "description": item.get("description", item.get("text", "")),
                "url": item.get("url", item.get("link", item.get("apply_url", "#"))),
                "location": item.get("location", item.get("candidate_required_location", "")),
                "platform": PLATFORM_HANDLERS.get(platform_key, {}).get("name", platform_key),
            })
        return results

    async def _parse_html(self, url: str, platform_key: str) -> list[dict[str, str]]:
        text = await self._fetch_text(url)
        soup = BeautifulSoup(text, "html.parser")
        cards = soup.find_all(["div", "li", "article"], class_=re.compile(
            r"(job|vaga|card|listing|result)", re.I
        ))
        if not cards:
            cards = soup.find_all(["div", "li", "article"])
        results = []
        for card in cards[:30]:
            title_el = card.find(["h2", "h3", "h4", "a"], class_=re.compile(r"(title|role|position|job)", re.I))
            if not title_el:
                title_el = card.find(["h2", "h3", "h4", "a"])
            link = card.find("a", href=True)
            url = ""
            if link:
                href = link["href"]
                url = href if href.startswith("http") else f"https://{href.lstrip('/')}"
            results.append({
                "title": title_el.get_text(strip=True) if title_el else "N/A",
                "company": "",
                "description": card.get_text(strip=True)[:500],
                "url": url,
                "location": "",
                "platform": PLATFORM_HANDLERS.get(platform_key, {}).get("name", platform_key),
            })
        return results
