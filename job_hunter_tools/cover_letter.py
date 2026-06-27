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

_TOOL_PARAMS = tool_parameters_schema(
    letter_data=StringSchema(
        'JSON string with letter content. body_paragraphs must be ARRAY of strings. '
        "Structure: "
        "{recruiter_name, recruiter_email, company, job_title, "
        'body_paragraphs: [str], name, contact: {email, phone, linkedin}}',
    ),
    template_lang=StringSchema(
        "Template language: 'pt-br' for Portuguese, 'en' for English",
    ),
    output_format=StringSchema(
        "Output format: 'text' for plain text (copy-paste ready), 'pdf' for formal PDF letter",
    ),
    required=["letter_data"],
)


@tool_parameters(_TOOL_PARAMS)
class CoverLetterTool(Tool):
    name = "cover_letter"
    description = (
        "Gera carta de apresentação ou e-mail personalizado para uma vaga. "
        "Pode retornar texto formatado (para copiar e colar no LinkedIn/e-mail) "
        "ou PDF (para candidatura formal). "
        "O parâmetro letter_data deve conter um JSON com os dados da carta."
    )

    @property
    def read_only(self) -> bool:
        return False

    async def execute(
        self,
        letter_data: str,
        template_lang: str = "pt-br",
        output_format: str = "text",
        **kwargs: Any,
    ) -> str:
        try:
            data = json.loads(letter_data) if isinstance(letter_data, str) else letter_data
        except json.JSONDecodeError as e:
            return f"Error: JSON inválido em letter_data: {e}"

        data = self._coerce_types(data)

        template_file = TEMPLATES_DIR / f"email.{template_lang}.html"
        if not template_file.exists():
            return f"Error: Template não encontrado: {template_file}"

        html_template = template_file.read_text(encoding="utf-8")
        template = Template(html_template)
        html_content = template.render(**data)

        if output_format == "text":
            text = self._html_to_plain_text(html_content)
            return f"Carta gerada:\n\n{text}"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"cover-letter-{template_lang}.pdf"

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

        return f"PDF gerado: {output_path}\n\n---\n\n{self._html_to_plain_text(html_content)}"

    def _html_to_plain_text(self, html: str) -> str:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

    def _coerce_types(self, data: dict) -> dict:
        data = dict(data)
        paragraphs = data.get("body_paragraphs")
        if isinstance(paragraphs, str):
            data["body_paragraphs"] = [paragraphs]
        elif paragraphs is None:
            data["body_paragraphs"] = []
        return data
