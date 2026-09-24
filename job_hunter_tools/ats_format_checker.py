from __future__ import annotations

import json
import os
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema

from .ats.format_check import ATSFormatCheck

_SEVERITY_ICONS = {
    "error": "❌",
    "warning": "⚠️",
    "info": "💡",
}

_CHECK_LABELS = {
    "personal_data": "Dados Pessoais",
    "objective_section": "Seção Objetivo",
    "references_section": "Referências",
    "obsolete_skill": "Skill Desatualizada",
    "low_bullet_ratio": "Uso de Bullet Points",
    "too_many_pages": "Número de Páginas",
}

_TOOL_PARAMS = tool_parameters_schema(
    txt_path=StringSchema(
        "Caminho absoluto para o arquivo .txt gerado junto com o PDF.",
    ),
    pdf_path=StringSchema(
        "Caminho absoluto para o PDF gerado. Opcional — necessário para verificar número de páginas.",
    ),
    is_beginner=StringSchema(
        "'true' se o usuário tem menos de 2 anos de experiência. "
        "Ativa verificação de página única. (default 'false')",
    ),
    required=[],
)


@tool_parameters(_TOOL_PARAMS)
class ATSFormatCheckerTool(Tool):
    name = "ats_format_check"
    description = (
        "Verifica formatação e boas práticas ATS no currículo gerado. "
        "Analisa o .txt e opcionalmente o PDF para detectar: dados pessoais "
        "(CPF, RG, data de nascimento, estado civil), seções obsoletas "
        "('Objetivo', 'Referências disponíveis'), skills desatualizadas "
        "(jQuery, AngularJS, Flash), baixo uso de bullet points, e "
        "currículo com mais de 1 página para iniciantes. "
        "Use APÓS resume_generator e ats_validator."
    )

    @property
    def read_only(self) -> bool:
        return True

    async def execute(
        self,
        txt_path: str = "",
        pdf_path: str = "",
        is_beginner: str = "false",
        **kwargs: Any,
    ) -> str:
        if not txt_path:
            return "❌ Informe o caminho do .txt com txt_path=..."

        if not os.path.exists(txt_path):
            return f"❌ Arquivo não encontrado: {txt_path}"

        checker = ATSFormatCheck()
        beginner = is_beginner.lower() == "true"
        pdf = pdf_path if pdf_path and os.path.exists(pdf_path) else None

        result = checker.run_all(
            txt_path=txt_path,
            pdf_path=pdf,
            is_beginner=beginner,
        )

        if "error" in result:
            return f"❌ Erro: {result['error']}"

        lines: list[str] = []
        lines.append("📋 VERIFICAÇÃO DE FORMATAÇÃO ATS")
        lines.append(f"{'━' * 52}")
        lines.append("")

        if not result["has_issues"]:
            lines.append("✅ Nenhum problema de formatação encontrado.")
            lines.append("")
            lines.append(f"{'━' * 52}")
            return "\n".join(lines)

        lines.append(f"Total: {result['total_issues']} "
                      f"(❌ {result['errors']} | ⚠️ {result['warnings']} | 💡 {result['infos']})")
        lines.append("")

        for check in result["checks"]:
            severity = check.get("severity", "info")
            icon = _SEVERITY_ICONS.get(severity, "•")
            check_type = check.get("type", "")
            label = _CHECK_LABELS.get(check_type, check_type)
            title = check.get("title", "")
            preview = check.get("preview", "")
            suggestion = check.get("suggestion", "")

            lines.append(f"{icon} **{title}**")
            if preview:
                lines.append(f"   → {preview}")
            lines.append(f"   💬 {suggestion}")
            lines.append("")

        lines.append(f"{'━' * 52}")
        lines.append("Corrija os problemas acima e regenere o currículo.")

        return "\n".join(lines)
