from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .keywords import SkillsDict
from .preprocessor import clean_text


def keyword_match(
    resume_text: str,
    jd_text: str,
    skills_dict: SkillsDict | None = None,
    lang: str = "pt-br",
) -> dict[str, Any]:
    if skills_dict is None:
        skills_dict = SkillsDict()

    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()

    jd_skills = skills_dict.find_all_matches(jd_text)
    resume_skills = skills_dict.find_all_matches(resume_text)

    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)
    extra = sorted(resume_skills - jd_skills)

    match_rate = round(len(matched) / len(jd_skills) * 100, 1) if jd_skills else 0.0

    return {
        "match_rate": match_rate,
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
        "jd_skill_count": len(jd_skills),
        "resume_skill_count": len(resume_skills),
    }


def keyword_match_weighted(
    resume_text: str,
    jd_text: str,
    skills_dict: SkillsDict | None = None,
    lang: str = "pt-br",
    required_skills: list[str] | None = None,
    desirable_skills: list[str] | None = None,
) -> dict[str, Any]:
    if skills_dict is None:
        skills_dict = SkillsDict()

    resume_skills = skills_dict.find_all_matches(resume_text)

    result: dict[str, Any] = {}

    if required_skills is not None:
        required_set = set(required_skills)
        req_matched = sorted(required_set & resume_skills)
        req_missing = sorted(required_set - resume_skills)
        result["required"] = {
            "matched": req_matched,
            "missing": req_missing,
            "total": len(required_set),
            "score": round(len(req_matched) / len(required_set) * 100, 1) if required_set else 0.0,
        }
    else:
        result["required"] = None

    if desirable_skills is not None:
        desirable_set = set(desirable_skills)
        des_matched = sorted(desirable_set & resume_skills)
        des_missing = sorted(desirable_set - resume_skills)
        result["desirable"] = {
            "matched": des_matched,
            "missing": des_missing,
            "total": len(desirable_set),
            "score": round(len(des_matched) / len(desirable_set) * 100, 1) if desirable_set else 0.0,
        }
    else:
        result["desirable"] = None

    jd_skills = skills_dict.find_all_matches(jd_text)
    all_matched = sorted(jd_skills & resume_skills)
    all_missing = sorted(jd_skills - resume_skills)

    result["all_matched"] = all_matched
    result["all_missing"] = all_missing
    result["jd_skill_count"] = len(jd_skills)
    result["resume_skill_count"] = len(resume_skills)

    return result


def tfidf_similarity(resume_text: str, jd_text: str, lang: str = "pt-br") -> float:
    resume_clean = clean_text(resume_text, lang)
    jd_clean = clean_text(jd_text, lang)

    try:
        vec = TfidfVectorizer(
            stop_words=list(_get_combined_stopwords(lang)),
            ngram_range=(1, 2),
            max_features=1000,
            sublinear_tf=True,
        )
        vectors = vec.fit_transform([resume_clean, jd_clean])
        score = cosine_similarity(vectors[0], vectors[1])[0][0]
        return round(float(score) * 100, 2)
    except ValueError:
        return 0.0


def _get_combined_stopwords(lang: str) -> set[str]:
    from .preprocessor import load_stopwords
    return load_stopwords(include_pt=(lang == "pt-br"), include_en=True)
