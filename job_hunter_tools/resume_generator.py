from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from jinja2 import Template
from playwright.async_api import async_playwright

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema

TEMPLATES_DIR = Path(os.environ.get("JOB_HUNTER_TEMPLATES", str(Path(__file__).parent.parent / "templates")))
OUTPUT_DIR = Path(os.environ.get("JOB_HUNTER_OUTPUT", str(Path.home() / ".nanobot" / "workspace" / "output")))

DTO_EXAMPLE = '''{
  "name": "John Doe",
  "role": "Software Engineer",
  "contact": { "email": "john@email.com", "phone": "+55 11 ...", "linkedin": "john", "github": "john" },
  "about": "Full stack developer with 10+ years...",
  "experiences": [
    { "company": "ACME Corp", "role": "Backend Engineer", "period": "2021-2025",
      "description": "Built scalable APIs...",
      "highlights": ["Reduced latency by 50%", "Led team of 3"] }
  ],
  "projects": [
    { "name": "My App", "description": "A mobile app...", "technologies": ["React Native", "Node.js"] }
  ],
  "skills": ["TypeScript", "Python", "AWS"],
  "education": [
    { "institution": "MIT", "degree": "BSc Computer Science", "period": "2015-2019" }
  ],
  "activities": [
    { "name": "SBC Programming Marathon", "year": "2013",
      "description": "Problem-solving developer...",
      "technologies": ["Java"], "url": "https://..." }
  ]
}'''

_TOOL_PARAMS = tool_parameters_schema(
    resume_data=StringSchema(
        'JSON string with resume content. Use EXACT data types: '
        'experiences is ARRAY of objects, highlights is ARRAY of strings, '
        'projects is ARRAY of objects, technologies is ARRAY of strings, '
        'skills is ARRAY of strings, education is ARRAY of objects, '
        'activities is OPTIONAL ARRAY of objects (omit completely if none). '
        'Follow this structure exactly (fields are optional but types must match): ' + DTO_EXAMPLE,
    ),
    template_lang=StringSchema(
        "Template language: 'pt-br' for Portuguese, 'en' for English",
    ),
    job_title=StringSchema(
        "Job title for the filename. Will generate '<job_title> - <name>.pdf'",
    ),
    required=["resume_data", "job_title"],
)


@tool_parameters(_TOOL_PARAMS)
class ResumeGeneratorTool(Tool):
    name = "resume_generator"
    description = (
        "Gera um currículo em PDF a partir de dados JSON. "
        "Usa template HTML com Tailwind CSS renderizado via Playwright (Chrome headless). "
        "O parâmetro resume_data deve conter um JSON com os dados do currículo."
    )

    @property
    def read_only(self) -> bool:
        return False

    async def execute(self, resume_data: str, template_lang: str = "pt-br", job_title: str = "", **kwargs: Any) -> str:
        try:
            data = json.loads(resume_data) if isinstance(resume_data, str) else resume_data
        except json.JSONDecodeError as e:
            return f"Error: JSON inválido em resume_data: {e}"

        data = self._coerce_types(data)

        filename = ""
        name_slug = data.get("name", "").strip()
        title_slug = job_title.strip() if job_title else ("curriculo" if template_lang == "pt-br" else "resume")
        if name_slug and title_slug:
            filename = f"{title_slug} - {name_slug}"
        elif title_slug:
            filename = title_slug
        else:
            filename = "curriculo" if template_lang == "pt-br" else "resume"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{filename}.pdf"

        template_file = TEMPLATES_DIR / f"resume.{template_lang}.html"
        if not template_file.exists():
            return f"Error: Template não encontrado: {template_file}"

        html_template = template_file.read_text(encoding="utf-8")
        template = Template(html_template)
        html_content = template.render(**data)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.set_content(html_content, wait_until="networkidle")
                await page.pdf(
                    path=str(output_path),
                    format="A4",
                    print_background=True,
                )
                await browser.close()
        except Exception as e:
            return f"Error ao gerar PDF: {e}"

        return f"PDF gerado: {output_path}"

    def _coerce_types(self, data: dict) -> dict:
        data = dict(data)

        array_of_string_fields = ["skills"]
        for key in array_of_string_fields:
            val = data.get(key)
            if isinstance(val, str):
                data[key] = [val]
            elif val is None:
                data[key] = []

        array_of_objects_fields = ["experiences", "projects", "education", "activities"]
        for key in array_of_objects_fields:
            val = data.get(key)
            if isinstance(val, dict):
                data[key] = [val]
            elif val is None:
                data[key] = []

        for exp in data.get("experiences", []):
            if isinstance(exp, dict):
                h = exp.get("highlights")
                if isinstance(h, str):
                    exp["highlights"] = [h]
                elif h is None:
                    exp["highlights"] = []

        for act in data.get("activities", []):
            if isinstance(act, dict):
                t = act.get("technologies")
                if isinstance(t, str):
                    act["technologies"] = [t]
                elif t is None:
                    act["technologies"] = []

        for proj in data.get("projects", []):
            if isinstance(proj, dict):
                t = proj.get("technologies")
                if isinstance(t, str):
                    proj["technologies"] = [t]
                elif t is None:
                    proj["technologies"] = []

        return data
