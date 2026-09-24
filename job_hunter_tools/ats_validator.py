from __future__ import annotations

import json
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema

from .ats.engine import ATSEngine

_TOOL_PARAMS = tool_parameters_schema(
    resume_path=StringSchema(
        "Caminho absoluto para o arquivo PDF (ou .txt) do currículo gerado.",
    ),
    job_description=StringSchema(
        "Texto completo da descrição da vaga. "
        "Deve conter os requisitos, responsabilidades e diferenciais.",
    ),
    lang=StringSchema(
        "Idioma do currículo e vaga: 'pt-br' para português (default), 'en' para inglês",
    ),
    resume_md_path=StringSchema(
        "Caminho para o arquivo RESUME.md original. Quando fornecido, "
        "permite classificar skills ausentes como 'presentes no RESUME.md' vs 'não encontradas'.",
    ),
    required_headers=StringSchema(
        "JSON array com os cabeçalhos das seções de requisitos obrigatórios. "
        "Ex: '[\"Requisitos\", \"Obrigatórios\"]'. Se não informado, "
        "a tool tenta detectar automaticamente.",
    ),
    desirable_headers=StringSchema(
        "JSON array com os cabeçalhos das seções de diferenciais. "
        "Ex: '[\"Diferenciais\", \"Nice to Have\"]'. Se não informado, "
        "a tool tenta detectar automaticamente.",
    ),
    culture_terms=StringSchema(
        "JSON array com termos de cultura da empresa pesquisados pelo agente "
        "(site, LinkedIn, Glassdoor). Ex: '[\"autonomia\", \"ownership\", "
        "\"colaboração\", \"experimentação\"]'. A tool verifica se aparecem "
        "no currículo e sugere inclusão.",
    ),
    required=["resume_path", "job_description"],
)


_GAP_ICONS = {
    "in_resume": "✅",
    "in_generated": "🟢",
    "related_in_resume": "⚠️",
    "not_in_resume": "❌",
}

_GAP_LABELS = {
    "in_resume": "está no RESUME.md. Adicione ao JSON antes de gerar.",
    "in_generated": "já está no currículo gerado.",
    "related_in_resume": "não explícito, mas há skill relacionada no RESUME.md. Considere adicionar menção.",
    "not_in_resume": "não está no seu currículo. Tem experiência para adicionar?",
}


@tool_parameters(_TOOL_PARAMS)
class ATSValidatorTool(Tool):
    name = "ats_validator"
    description = (
        "Analisa um currículo PDF (ou .txt) contra uma descrição de vaga "
        "e retorna relatório completo: score ATS com pesos por tipo de skill "
        "(obrigatórias vs diferenciais), TF-IDF, similaridade semântica "
        "(Sentence-Transformers), classificação individual de cada skill ausente "
        "e sugestões de melhoria. "
        "Opcionalmente aceita o RESUME.md original para cruzar skills faltantes. "
        "Use APÓS gerar o currículo com resume_generator."
    )

    @property
    def read_only(self) -> bool:
        return True

    async def execute(
        self,
        resume_path: str,
        job_description: str,
        lang: str = "pt-br",
        resume_md_path: str | None = None,
        required_headers: str | None = None,
        desirable_headers: str | None = None,
        culture_terms: str | None = None,
        **kwargs: Any,
    ) -> str:
        engine = ATSEngine()

        parsed_required: list[str] | None = None
        parsed_desirable: list[str] | None = None
        parsed_culture: list[str] | None = None
        if required_headers:
            try:
                parsed_required = json.loads(required_headers)
            except (json.JSONDecodeError, TypeError):
                pass
        if desirable_headers:
            try:
                parsed_desirable = json.loads(desirable_headers)
            except (json.JSONDecodeError, TypeError):
                pass
        if culture_terms:
            try:
                parsed_culture = json.loads(culture_terms)
            except (json.JSONDecodeError, TypeError):
                pass

        result = engine.analyze(
            resume_path=resume_path,
            job_description=job_description,
            lang=lang,
            resume_md_path=resume_md_path,
            required_headers=parsed_required,
            desirable_headers=parsed_desirable,
            culture_terms=parsed_culture,
        )

        if "error" in result:
            return f"❌ Erro: {result['error']}"

        source_label = "PDF" if result.get("source") == "pdf" else "TXT"
        word_count = result.get("resume_word_count", 0)
        bd = result.get("breakdown", {})
        skills = result.get("skills", {})
        sem = result.get("semantic")
        vocab = result.get("vocabulary")
        culture = result.get("culture")
        components = result.get("components", [])
        gap_class = skills.get("gap_classification", {})

        lines: list[str] = []

        lines.append("📊 RELATÓRIO COMPLETO DE ANÁLISE ATS")
        lines.append(f"{'━' * 52}")
        lines.append("")

        lines.append(f"🎯 SCORE GERAL: {result['overall_score']}% ({result['match_label'].strip()})")
        for c in components:
            label = c["label"]
            score = c["score"]
            weight = c["weight"]
            lines.append(f"   {_comp_icon(c['key'])} {label}: {score}%  (peso {int(weight * 100)}%)")
        lines.append("")

        lines.append("📄 INFORMAÇÕES DO DOCUMENTO")
        lines.append(f"   Fonte: {source_label} | {word_count} palavras")
        lines.append("")

        jd_class = result.get("jd_classification", {})
        all_required = jd_class.get("required", [])
        all_desirable = jd_class.get("desirable", [])

        matched = skills.get("matched", [])
        if matched:
            lines.append(f"✅ SKILLS ENCONTRADAS ({len(matched)})")
            for s in matched:
                tag = ""
                if s in all_required:
                    tag = " [OBRIGATÓRIA]"
                elif s in all_desirable:
                    tag = " [DIFERENCIAL]"
                lines.append(f"   • {s}{tag}")
        else:
            lines.append("✅ Nenhuma skill encontrada no dicionário.")
        lines.append("")

        missing = skills.get("missing", [])
        if missing:
            lines.append(f"❌ SKILLS AUSENTES ({len(missing)})")
            for s in missing:
                tag = ""
                if s in all_required:
                    tag = " [OBRIGATÓRIA]"
                elif s in all_desirable:
                    tag = " [DIFERENCIAL]"

                gap_status = gap_class.get(s)
                if gap_status:
                    icon = _GAP_ICONS.get(gap_status, "•")
                    label = _GAP_LABELS.get(gap_status, "")
                    lines.append(f"   {icon} {s}{tag} → {label}")
                else:
                    lines.append(f"   • {s}{tag}")
        else:
            lines.append("❌ Nenhuma skill ausente — cobertura total!")
        lines.append("")

        if sem:
            lines.append("🧠 ANÁLISE SEMÂNTICA")
            lines.append(f"   Similaridade: {sem['score']}%")
            lines.append(f"   Modelo: {sem['model']}")
            lines.append(f"   {sem['note']}")
            lines.append("")

        if vocab:
            gaps = vocab.get("gaps", [])
            lines.append("🔤 ANÁLISE DE VOCABULÁRIO (TF-IDF)")
            lines.append(f"   Score: {vocab['score']}% de termos compartilhados")
            lines.append(f"   Termos únicos da JD: {vocab['total_jd_terms']} | "
                         f"Presentes no currículo: {vocab['shared_terms']}")
            if gaps:
                lines.append("")
                lines.append("   Termos da JD ausentes no seu texto "
                             "(incorpore naturalmente nas descrições):")
                for g in gaps[:8]:
                    lines.append(f"   • \"{g['term']}\" ({g['count']}x na vaga)")
            lines.append("")

        if culture:
            lines.append("🏢 TERMOS DE CULTURA DA EMPRESA")
            for r in culture.get("results", []):
                icon = "✅" if r["found"] else "❌"
                lines.append(f"   {icon} {r['term']}")
            if culture.get("score", 100) < 100:
                lines.append("")
                lines.append("   Considere incluir os termos ausentes se "
                             "eles refletem seus valores profissionais.")
            lines.append("")

        suggestions = result.get("suggestions", [])
        if suggestions:
            lines.append("💡 RECOMENDAÇÕES")
            for tip in suggestions:
                lines.append(f"   • {tip}")
            lines.append("")

        level = result.get("match_level", "baixo")
        lines.append(f"{'━' * 52}")
        if level == "alto":
            lines.append("✅ Pode enviar o currículo — match alto com a vaga.")
        elif level == "medio":
            lines.append("🤔 Match médio — revise as skills classificadas acima.")
            lines.append("   Skills ✅ no RESUME.md: adicione ao JSON e regenere.")
            lines.append("   Skills ❌ não encontradas: pergunte ao usuário.")
            lines.append("   Depois de ajustar, reexecute ats_validator para confirmar.")
        else:
            lines.append("🎯 Match baixo — considere ajustar o currículo ou buscar outra vaga.")

        return "\n".join(lines)


def _comp_icon(key: str) -> str:
    return {"required": "📝", "desirable": "📎", "semantic": "🧠", "tfidf": "🔤", "vocabulary": "📖"}.get(key, "•")
