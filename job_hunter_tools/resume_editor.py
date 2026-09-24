from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema

RESUME_PATH = Path(os.environ.get("JOB_HUNTER_RESUME_PATH", str(Path.home() / ".nanobot" / "workspace" / "RESUME.md")))
WORKSPACE_RESUME_PATH = Path(os.environ.get("JOB_HUNTER_WORKSPACE_RESUME_PATH", str(Path.home() / ".nanobot" / "workspace" / "RESUME.md")))

_TOOL_PARAMS = tool_parameters_schema(
    resume_content=StringSchema(
        "Full markdown content for RESUME.md. Must include ALL sections (Information, About, Experience, Projects, Skills, Education, etc.). "
        "This REPLACES the entire file — do not send partial content.",
    ),
    changes_summary=StringSchema(
        "Brief description of what changed (e.g., 'Added new experience at Google'). Optional but recommended for logging.",
    ),
    required=["resume_content"],
)


@tool_parameters(_TOOL_PARAMS)
class ResumeEditorTool(Tool):
    name = "resume_editor"
    description = (
        "Escreve o conteúdo completo do currículo no RESUME.md. "
        "O parâmetro resume_content deve conter o markdown COMPLETO do currículo, "
        "pois substitui TODO o arquivo. Sempre inclua todas as seções existentes "
        "com as alterações desejadas. Após escrever, retorna confirmação com o "
        "caminho do arquivo e um resumo das mudanças."
    )

    @property
    def read_only(self) -> bool:
        return False

    async def execute(
        self,
        resume_content: str,
        changes_summary: str = "",
        **kwargs: Any,
    ) -> str:
        return self._write_sync(resume_content, changes_summary)

    def _write_sync(self, content: str, summary: str) -> str:
        targets = []

        RESUME_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESUME_PATH.write_text(content, encoding="utf-8")
        targets.append(str(RESUME_PATH))

        workspace_path = self._resolve_workspace_path()
        if workspace_path and workspace_path != RESUME_PATH:
            workspace_path.parent.mkdir(parents=True, exist_ok=True)
            workspace_path.write_text(content, encoding="utf-8")
            targets.append(str(workspace_path))

        lines = content.strip().split("\n")
        preview_lines = lines[:5] if len(lines) > 5 else lines
        preview = "\n".join(preview_lines)

        parts = [f"✅ RESUME.md atualizado ({len(lines)} linhas)"]
        parts.append(f"   Arquivos: {', '.join(targets)}")
        if summary:
            parts.append(f"   Mudanças: {summary}")
        parts.append(f"\nPrimeiras linhas:\n{preview}")

        return "\n".join(parts)

    def _resolve_workspace_path(self) -> Path | None:
        if WORKSPACE_RESUME_PATH != RESUME_PATH:
            return WORKSPACE_RESUME_PATH
        return None
