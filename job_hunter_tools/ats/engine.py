from __future__ import annotations

import os
from typing import Any

from .jd_parser import classify_jd_skills
from .keywords import SkillsDict
from .parser import extract_text
from .scorer import calculate_score
from .semantic import SemanticMatcher
from .vocabulary import analyze_culture_terms, analyze_vocabulary_gaps


class ATSEngine:
    def __init__(self, skills_dict: SkillsDict | None = None) -> None:
        self.skills_dict = skills_dict or SkillsDict()
        self._semantic: SemanticMatcher | None = None

    @property
    def semantic(self) -> SemanticMatcher:
        if self._semantic is None:
            self._semantic = SemanticMatcher()
        return self._semantic

    def analyze(
        self,
        resume_path: str,
        job_description: str,
        lang: str = "pt-br",
        use_semantic: bool = True,
        resume_md_path: str | None = None,
        required_headers: list[str] | None = None,
        desirable_headers: list[str] | None = None,
        culture_terms: list[str] | None = None,
    ) -> dict[str, Any]:
        if not os.path.exists(resume_path):
            return {
                "error": f"Arquivo não encontrado: {resume_path}",
                "overall_score": 0.0,
                "match_level": "erro",
            }

        companion_txt = self._find_companion_txt(resume_path)
        source = "pdf"
        try:
            if companion_txt and os.path.exists(companion_txt):
                resume_text = extract_text(companion_txt)
                source = "txt"
            else:
                resume_text = extract_text(resume_path)
                source = "pdf"
                word_count = len(resume_text.split())
                if word_count < 50:
                    txt_fallback = self._find_any_txt_nearby(resume_path)
                    if txt_fallback:
                        resume_text = extract_text(txt_fallback)
                        source = "txt"
        except Exception as e:
            return {
                "error": f"Erro ao extrair texto: {e}",
                "overall_score": 0.0,
                "match_level": "erro",
            }

        jd_classification = classify_jd_skills(
            jd_text=job_description,
            skills_dict=self.skills_dict,
            lang=lang,
            required_headers_override=required_headers,
            desirable_headers_override=desirable_headers,
        )

        resume_md_text: str | None = None
        if resume_md_path and os.path.exists(resume_md_path):
            try:
                resume_md_text = extract_text(resume_md_path)
            except Exception:
                pass

        semantic_score: float | None = None
        semantic_gaps: dict[str, Any] | None = None
        if use_semantic:
            semantic_score = self.semantic.compute_similarity(resume_text, job_description)
            semantic_gaps = self.semantic.find_gaps(resume_text, job_description, lang=lang)

        vocabulary_gaps_result = analyze_vocabulary_gaps(resume_text, job_description, lang)

        culture_result = None
        if culture_terms:
            culture_result = analyze_culture_terms(resume_text, culture_terms)

        result = calculate_score(
            resume_text=resume_text,
            jd_text=job_description,
            lang=lang,
            skills_dict=self.skills_dict,
            semantic_score=semantic_score,
            required_skills=jd_classification["required"],
            desirable_skills=jd_classification["desirable"],
            resume_md_text=resume_md_text,
            vocabulary_gaps_result=vocabulary_gaps_result,
            culture_result=culture_result,
            semantic_gaps=semantic_gaps,
        )

        result["source"] = source
        result["resume_word_count"] = len(resume_text.split())
        result["semantic_available"] = semantic_score is not None
        if semantic_gaps:
            result["semantic_gaps"] = semantic_gaps
        result["jd_classification"] = jd_classification

        if source == "pdf":
            result.setdefault("suggestions", []).insert(
                0,
                "O texto foi extraído do PDF. A qualidade pode ser inferior ao .txt "
                "companheiro. Considere gerar o currículo com ats_txt=true.",
            )

        return result

    def _find_companion_txt(self, pdf_path: str) -> str | None:
        base, _ = os.path.splitext(pdf_path)
        txt_path = base + ".txt"
        if os.path.exists(txt_path):
            return txt_path
        base_no_suffix = base.rstrip(" -") if " - " in base else base
        alt_clean = base_no_suffix + ".txt"
        if alt_clean != txt_path and os.path.exists(alt_clean):
            return alt_clean
        alt_spaced = base.replace(" - ", " - ") + ".txt"
        if alt_spaced != txt_path and os.path.exists(alt_spaced):
            return alt_spaced
        return None

    def _find_any_txt_nearby(self, path: str) -> str | None:
        from pathlib import Path as PlibPath
        d = PlibPath(path).parent
        for f in sorted(d.glob("*.txt")):
            return str(f)
        return None
