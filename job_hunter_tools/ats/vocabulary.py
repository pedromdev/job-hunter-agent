from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .preprocessor import clean_text


def analyze_vocabulary_gaps(
    resume_text: str,
    jd_text: str,
    lang: str = "pt-br",
    top_n: int = 15,
) -> dict[str, Any]:
    resume_clean = clean_text(resume_text, lang)
    jd_clean = clean_text(jd_text, lang)

    resume_tokens = set(resume_clean.split())
    jd_tokens = jd_clean.split()

    jd_counter = Counter(jd_tokens)

    gaps = [
        {"term": word, "count": count}
        for word, count in jd_counter.most_common(80)
        if len(word) > 2
        and count >= 2
        and word not in resume_tokens
        and not _looks_like_stopword(word)
    ][:top_n]

    return {
        "gaps": gaps,
        "total_jd_terms": len(jd_counter),
        "shared_terms": len(resume_tokens & set(jd_counter.keys())),
        "score": round(
            len(resume_tokens & set(jd_counter.keys()))
            / max(len(set(jd_counter.keys())), 1)
            * 100,
            1,
        ),
    }


def analyze_culture_terms(
    resume_text: str,
    culture_terms: list[str],
) -> dict[str, Any]:
    resume_lower = resume_text.lower()
    results: list[dict[str, str | bool]] = []

    for term in culture_terms:
        term_lower = term.lower().strip()
        found = term_lower in resume_lower
        results.append({
            "term": term,
            "found": found,
        })

    found_count = sum(1 for r in results if r["found"])
    score = round(found_count / max(len(results), 1) * 100, 1)

    return {
        "results": results,
        "found_count": found_count,
        "total": len(results),
        "score": score,
    }


_EXTRA_STOP = {
    "você", "voce", "aqui", "além", "ainda", "através", "através", "cada",
    "coisa", "coisas", "como", "deve", "devem", "durante", "forma",
    "grande", "isso", "isto", "maior", "mais", "melhor", "menos",
    "mesma", "mesmo", "muito", "muitos", "naquela", "naquele", "nela",
    "nele", "nelas", "dela", "dele", "delas", "deles", "nível",
    "nova", "novo", "novos", "onde", "outra", "outro", "outras",
    "outros", "pode", "podem", "poder", "pois", "porque", "possuem",
    "própria", "próprio", "qual", "quais", "quando", "quanto",
    "que", "quem", "sempre", "ser", "sido", "sua", "suas", "seu", "seus",
    "tal", "tais", "também", "tambem", "toda", "todo", "todos", "tudo",
    "tão", "única", "único", "uma", "umas", "vai", "vezes", "através",
}


def _looks_like_stopword(word: str) -> bool:
    if re.match(r"^\d+$", word):
        return True
    if len(word) <= 2:
        return True
    if word in _EXTRA_STOP:
        return True
    return False
