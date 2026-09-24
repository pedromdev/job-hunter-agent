from __future__ import annotations

from typing import Any

from .keywords import SkillsDict
from .matcher import keyword_match_weighted, tfidf_similarity

SCORE_THRESHOLDS = {
    "alto": 70.0,
    "medio": 40.0,
    "baixo": 0.0,
}


def calculate_score(
    resume_text: str,
    jd_text: str,
    lang: str = "pt-br",
    skills_dict: SkillsDict | None = None,
    semantic_score: float | None = None,
    semantic_gaps: dict[str, Any] | None = None,
    required_skills: list[str] | None = None,
    desirable_skills: list[str] | None = None,
    resume_md_text: str | None = None,
    vocabulary_gaps_result: dict[str, Any] | None = None,
    culture_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if skills_dict is None:
        skills_dict = SkillsDict()

    kw_result = keyword_match_weighted(
        resume_text=resume_text,
        jd_text=jd_text,
        skills_dict=skills_dict,
        lang=lang,
        required_skills=required_skills,
        desirable_skills=desirable_skills,
    )
    tfidf_score = tfidf_similarity(resume_text, jd_text, lang)
    has_semantic = semantic_score is not None

    # Vocabulary score = % of JD terms present in resume
    vocab_score = vocabulary_gaps_result["score"] if vocabulary_gaps_result else 0.0
    # Culture score: what the agent found about the company
    culture_score = culture_result["score"] if culture_result else 0.0

    breakdown: dict[str, Any] = {
        "tfidf_score": tfidf_score,
    }

    components: list[dict[str, Any]] = []

    if kw_result["required"] is not None:
        r = kw_result["required"]
        components.append({
            "key": "required",
            "label": "Obrigatórias",
            "score": r["score"],
            "weight": 0.45,
        })
        breakdown["required_match"] = r["score"]

    if kw_result["desirable"] is not None:
        d = kw_result["desirable"]
        components.append({
            "key": "desirable",
            "label": "Diferenciais",
            "score": d["score"],
            "weight": 0.15,
        })
        breakdown["desirable_match"] = d["score"]

    if has_semantic:
        components.append({
            "key": "semantic",
            "label": "Semântico",
            "score": semantic_score,
            "weight": 0.25,
        })
        breakdown["semantic_score"] = semantic_score

    components.append({
        "key": "tfidf",
        "label": "TF-IDF",
        "score": tfidf_score,
        "weight": 0.10,
    })

    if vocabulary_gaps_result and vocab_score > 0:
        components.append({
            "key": "vocabulary",
            "label": "Vocabulário",
            "score": vocab_score,
            "weight": 0.05,
        })
        breakdown["vocabulary_score"] = vocab_score

    total_weight = sum(c["weight"] for c in components)
    if abs(total_weight - 1.0) > 0.01:
        for c in components:
            c["weight"] = round(c["weight"] / total_weight, 4)

    overall = round(sum(c["score"] * c["weight"] for c in components), 1)

    if overall >= SCORE_THRESHOLDS["alto"]:
        level = "alto"
        label = "🟢 Alto"
    elif overall >= SCORE_THRESHOLDS["medio"]:
        level = "medio"
        label = "🟡 Médio"
    else:
        level = "baixo"
        label = "🔴 Baixo"

    gap_classification: dict[str, str] | None = None
    if resume_md_text is not None:
        gap_classification = _classify_gaps(
            missing_skills=kw_result.get("all_missing", []),
            resume_text=resume_text,
            resume_md_text=resume_md_text,
            skills_dict=skills_dict,
        )

    suggestions = _build_suggestions(
        kw_result.get("all_missing", []),
        kw_result.get("all_matched", []),
        overall,
        level,
        resume_text,
        has_semantic,
        semantic_score,
        gap_classification,
        vocabulary_gaps_result,
        culture_result,
        semantic_gaps=semantic_gaps,
    )

    result: dict[str, Any] = {
        "overall_score": overall,
        "match_level": level,
        "match_label": label,
        "breakdown": breakdown,
        "components": components,
        "skills": {
            "matched": kw_result.get("all_matched", []),
            "missing": kw_result.get("all_missing", []),
            "jd_skill_count": kw_result.get("jd_skill_count", 0),
            "resume_skill_count": kw_result.get("resume_skill_count", 0),
        },
        "suggestions": suggestions,
    }

    if kw_result["required"] is not None:
        result["skills"]["required_matched"] = kw_result["required"]["matched"]
        result["skills"]["required_missing"] = kw_result["required"]["missing"]

    if kw_result["desirable"] is not None:
        result["skills"]["desirable_matched"] = kw_result["desirable"]["matched"]
        result["skills"]["desirable_missing"] = kw_result["desirable"]["missing"]

    if gap_classification:
        result["skills"]["gap_classification"] = gap_classification

    if has_semantic:
        result["semantic"] = {
            "score": semantic_score,
            "model": "paraphrase-multilingual-MiniLM-L12-v2",
            "note": _semantic_note(semantic_score),
        }

    if vocabulary_gaps_result:
        result["vocabulary"] = vocabulary_gaps_result

    if culture_result:
        result["culture"] = culture_result

    return result


def _classify_gaps(
    missing_skills: list[str],
    resume_text: str,
    resume_md_text: str,
    skills_dict: SkillsDict,
) -> dict[str, str]:
    resume_md_lower = resume_md_text.lower()
    resume_lower = resume_text.lower()

    classification: dict[str, str] = {}

    for skill in missing_skills:
        skill_variants = skills_dict.all_skills().get(skill, [skill.lower()])

        in_resume_md = any(v.lower() in resume_md_lower for v in [skill.lower()] + skill_variants)
        in_resume_text = any(v.lower() in resume_lower for v in [skill.lower()] + skill_variants)

        if in_resume_md:
            classification[skill] = "in_resume"
        elif in_resume_text:
            classification[skill] = "in_generated"
        else:
            related = _find_related_skill(skill, resume_md_text, skills_dict)
            if related:
                classification[skill] = "related_in_resume"
            else:
                classification[skill] = "not_in_resume"

    return classification


def _find_related_skill(skill: str, resume_md_text: str, skills_dict: SkillsDict) -> str | None:
    from difflib import SequenceMatcher
    resume_lower = resume_md_text.lower()

    for cat in skills_dict.categories:
        items = skills_dict._data.get(cat, {})
        if not isinstance(items, dict):
            continue
        for other_skill in items:
            if other_skill == skill:
                continue
            if other_skill.lower() in resume_lower:
                ratio = SequenceMatcher(None, skill.lower(), other_skill.lower()).ratio()
                if ratio > 0.3:
                    return other_skill
    return None


def _semantic_note(score: float) -> str:
    if score >= 80:
        return "Alta similaridade semântica — o contexto geral do currículo está muito alinhado com a vaga."
    elif score >= 60:
        return "Similaridade semântica moderada — o tema do currículo conversa com a vaga, mas gaps de termos específicos reduzem o score."
    elif score >= 40:
        return "Similaridade semântica baixa — o foco do currículo pode ser diferente do que a vaga pede."
    return "Similaridade semântica muito baixa — o currículo parece desconectado do contexto da vaga."


_GAP_LABELS: dict[str, str] = {
    "in_resume": "✅ está no RESUME.md. Adicione ao JSON antes de gerar.",
    "in_generated": "🟢 está no currículo atual. Pode manter.",
    "related_in_resume": "⚠️ não explícito, mas você tem skill relacionada no RESUME.md. Considere adicionar menção.",
    "not_in_resume": "❌ não está no seu currículo. Tem experiência para adicionar?",
}


def _build_suggestions(
    missing: list[str],
    matched: list[str],
    overall: float,
    level: str,
    resume_text: str,
    has_semantic: bool = False,
    semantic_score: float | None = None,
    gap_classification: dict[str, str] | None = None,
    vocabulary_gaps_result: dict[str, Any] | None = None,
    culture_result: dict[str, Any] | None = None,
    semantic_gaps: dict[str, Any] | None = None,
) -> list[str]:
    suggestions: list[str] = []

    if level == "alto":
        suggestions.append(
            "Ótimo match! O currículo cobre bem as skills da vaga. "
            "Verifique se as experiências e métricas estão bem destacadas."
        )
    elif level == "medio":
        suggestions.append(
            f"Match moderado ({overall}%). "
            "Veja abaixo a classificação de cada skill ausente."
        )
    else:
        suggestions.append(
            f"Match baixo ({overall}%). "
            "O currículo precisa de ajustes significativos para essa vaga."
        )

    if gap_classification and missing:
        has_in_resume = any(v == "in_resume" for v in gap_classification.values())
        has_not_in_resume = any(v == "not_in_resume" for v in gap_classification.values())

        if has_in_resume:
            suggestions.append(
                "Algumas skills ausentes já estão no RESUME.md — "
                "adicione-as ao JSON do currículo e regenere."
            )
        if has_not_in_resume:
            suggestions.append(
                "Pergunte ao usuário se ele tem experiência nas skills "
                "classificadas como ❌ não encontradas no currículo."
            )

    if vocabulary_gaps_result:
        gaps = vocabulary_gaps_result.get("gaps", [])
        if gaps:
            top_terms = [g["term"] for g in gaps[:5]]
            suggestions.append(
                "Termos da JD ausentes no seu texto: "
                + ", ".join(top_terms)
                + ". Considere incorporá-los naturalmente nas descrições."
            )

    if semantic_gaps:
        terms = semantic_gaps.get("missing_terms", [])
        if terms:
            suggestions.append(
                "Conceitos da vaga com baixa cobertura semântica: "
                + ", ".join(terms[:8])
                + ". Tente descrever experiências relacionadas a esses tópicos."
            )

    if culture_result:
        missing_culture = [r["term"] for r in culture_result.get("results", []) if not r["found"]]
        if missing_culture:
            suggestions.append(
                "Termos de cultura da empresa não encontrados: "
                + ", ".join(missing_culture[:5])
                + ". Se você se identifica com esses valores, mencione."
            )

    if has_semantic and semantic_score is not None:
        suggestions.append(_semantic_note(semantic_score))

    word_count = len(resume_text.split())
    if word_count < 200:
        suggestions.append(
            f"Currículo muito curto ({word_count} palavras). "
            "Expanda as descrições das experiências."
        )
    elif word_count > 1500:
        suggestions.append(
            f"Currículo extenso ({word_count} palavras). "
            "Considere condensar para 1-2 páginas."
        )

    if not suggestions:
        suggestions.append(
            "Currículo com boa cobertura. Destaque conquistas quantificáveis "
            "(ex: 'Melhorei performance em 30%')."
        )

    return suggestions
