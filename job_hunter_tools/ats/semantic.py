from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class SemanticMatcher:
    _instance: "SemanticMatcher | None" = None
    _model: Any = None
    _available: bool = False

    def __new__(cls) -> "SemanticMatcher":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def available(self) -> bool:
        return self._available

    def load(self) -> bool:
        if self._available:
            return True
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(_MODEL_NAME)
            self._available = True
            logger.info("SemanticMatcher loaded: %s", _MODEL_NAME)
            return True
        except Exception as e:
            logger.warning("SemanticMatcher unavailable (%s). Running without semantic scoring.", e)
            self._available = False
            return False

    def compute_similarity(self, resume_text: str, jd_text: str) -> float | None:
        if not self._available and not self.load():
            return None
        try:
            from sentence_transformers import util
            resume_emb = self._model.encode(resume_text, convert_to_tensor=True)
            jd_emb = self._model.encode(jd_text, convert_to_tensor=True)
            score = float(util.cos_sim(resume_emb, jd_emb).item()) * 100
            return round(score, 2)
        except Exception as e:
            logger.warning("Semantic similarity failed: %s", e)
            return None

    def find_gaps(
        self,
        resume_text: str,
        jd_text: str,
        threshold: float = 0.35,
        max_terms: int = 20,
        lang: str = "pt-br",
    ) -> dict[str, Any] | None:
        if not self._available and not self.load():
            return None
        try:
            from sentence_transformers import util

            resume_emb = self._model.encode(resume_text, convert_to_tensor=True)

            raw_parts = re.split(r"\n+|[.!?](?:\s|$)+", jd_text)
            sentences = [s.strip() for s in raw_parts if len(s.strip()) > 10]

            if not sentences:
                return {
                    "gap_sentences": [],
                    "missing_terms": [],
                    "covered_pct": 100.0,
                    "total_sentences": 0,
                    "gap_sentences_count": 0,
                }

            sent_embs = self._model.encode(sentences, convert_to_tensor=True)
            similarities = util.cos_sim(sent_embs, resume_emb).cpu().numpy().flatten()

            from .preprocessor import tokenize

            resume_tokens = set(tokenize(resume_text, lang))
            gap_sentences: list[dict[str, Any]] = []
            all_missing: list[str] = []

            for sent, sim in zip(sentences, similarities):
                sim_pct = round(float(sim) * 100, 1)
                if float(sim) >= threshold:
                    continue
                gap_sentences.append({"text": sent, "similarity": sim_pct})
                for token in tokenize(sent, lang):
                    if token not in resume_tokens and len(token) > 2:
                        all_missing.append(token)

            seen: set[str] = set()
            missing_terms: list[str] = []
            for t in all_missing:
                if t not in seen:
                    seen.add(t)
                    missing_terms.append(t)

            total = len(sentences)
            gap_count = len(gap_sentences)
            covered_pct = round((total - gap_count) / max(total, 1) * 100, 1)

            return {
                "gap_sentences": gap_sentences,
                "missing_terms": missing_terms[:max_terms],
                "covered_pct": covered_pct,
                "total_sentences": total,
                "gap_sentences_count": gap_count,
                "threshold": threshold,
            }
        except Exception as e:
            logger.warning("Semantic gap analysis failed: %s", e)
            return None
