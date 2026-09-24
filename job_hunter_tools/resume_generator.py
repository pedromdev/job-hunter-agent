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
  "name": "JOHN DOE",
  "about": "Resumo profissional adaptado à vaga, no padrão diagnóstico → proposta → decisão → execução → resultado...",
  "experiences": [
    { "company": "ACME Corp", "role": "Senior Full Stack Developer", "period": "2021-2025",
      "bullets": ["Diagnóstico: ... Proposta: ... Resultado: -50% latência", "..."] }
  ]
}'''

_TOOL_PARAMS = tool_parameters_schema(
    resume_data=StringSchema(
        'JSON string with resume content. The template is FIXED (header, education, '
        'technologies, languages and skills are baked in). The JSON controls only: '
        'name (used just for the output filename), '
        'about (string with the professional summary), and '
        'experiences (ARRAY of {company:string, role:string, period:string, '
        'bullets: ARRAY of strings}). '
        'Follow this structure exactly (fields are optional but types must match): ' + DTO_EXAMPLE,
    ),
    template_lang=StringSchema(
        "Template language: 'pt-br' for Portuguese, 'en' for English",
    ),
    job_title=StringSchema(
        "Job title for the filename. Will generate '<job_title> - <name>.pdf'",
    ),
    ats_txt=StringSchema(
        "Generate ATS-friendly .txt alongside PDF. 'true' or 'false' (default 'true')",
    ),
    required=["resume_data", "job_title"],
)


@tool_parameters(_TOOL_PARAMS)
class ResumeGeneratorTool(Tool):
    name = "resume_generator"
    description = (
        "Gera um currículo em PDF a partir de dados JSON. "
        "Usa template HTML renderizado via Playwright (Chrome headless). "
        "O template é fixo (cabeçalho, formação, tecnologias, idiomas e habilidades vêm do template). "
        "O JSON controla apenas 'about' e 'experiences' (role, company, period, bullets); "
        "'name' define o nome do arquivo."
    )

    @property
    def read_only(self) -> bool:
        return False

    async def execute(self, resume_data: str, template_lang: str = "pt-br", job_title: str = "", ats_txt: str = "true", **kwargs: Any) -> str:
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

        result = f"PDF gerado: {output_path}"

        if ats_txt.lower() == "true":
            try:
                txt_path = OUTPUT_DIR / f"{filename}.txt"
                txt_file = TEMPLATES_DIR / f"resume.{template_lang}.txt"
                if txt_file.exists():
                    txt_template = txt_file.read_text(encoding="utf-8")
                    template_txt = Template(txt_template)
                    txt_content = template_txt.render(**data)
                    txt_path.write_text(txt_content, encoding="utf-8")
                    result += f"\nATS .txt gerado: {txt_path}"
            except Exception as e:
                result += f"\nAviso: erro ao gerar .txt ATS: {e}"

        return result

    def _coerce_types(self, data: dict) -> dict:
        data = dict(data)

        array_of_string_fields = ["skills", "competencias"]
        for key in array_of_string_fields:
            val = data.get(key)
            if isinstance(val, str):
                data[key] = [val]
            elif val is None:
                data[key] = []

        array_of_objects_fields = ["experiences", "other_experiences", "projects", "education", "activities"]
        for key in array_of_objects_fields:
            val = data.get(key)
            if isinstance(val, dict):
                data[key] = [val]
            elif val is None:
                data[key] = []

        for exp in data.get("experiences", []):
            if isinstance(exp, dict):
                b = exp.get("bullets")
                if isinstance(b, str):
                    exp["bullets"] = [b]
                elif b is None:
                    exp["bullets"] = []

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

        destaques = data.get("destaques")
        if isinstance(destaques, dict):
            data["destaques"] = [destaques]
        elif destaques is None:
            data["destaques"] = []

        return data
