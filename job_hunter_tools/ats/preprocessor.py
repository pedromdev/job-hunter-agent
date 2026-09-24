import re
from pathlib import Path

_STOPWORDS_PT: set[str] | None = None
_STOPWORDS_EN: set[str] | None = None


def _load_stopwords(lang: str) -> set[str]:
    global _STOPWORDS_PT, _STOPWORDS_EN
    if lang == "pt" and _STOPWORDS_PT is not None:
        return _STOPWORDS_PT
    if lang == "en" and _STOPWORDS_EN is not None:
        return _STOPWORDS_EN

    data_dir = Path(__file__).parent / "data"
    filename = f"stopwords_{lang}.txt"
    filepath = data_dir / filename

    if not filepath.exists():
        try:
            import nltk
            from nltk.corpus import stopwords
            nltk.download("stopwords", quiet=True)
            words = set(stopwords.words("portuguese" if lang == "pt" else "english"))
        except ImportError:
            words = set()
    else:
        words = set(filepath.read_text(encoding="utf-8").strip().splitlines())

    if lang == "pt":
        _STOPWORDS_PT = words
    else:
        _STOPWORDS_EN = words
    return words


def load_stopwords(include_pt: bool = True, include_en: bool = True) -> set[str]:
    words: set[str] = set()
    if include_pt:
        words |= _load_stopwords("pt")
    if include_en:
        words |= _load_stopwords("en")
    return words


_TOKEN_PATTERN = re.compile(r"[‘’'´`]")
_STRIP_PATTERN_PT = re.compile(r"[^a-zA-ZÀ-ÿ0-9\s]")
_STRIP_PATTERN_EN = re.compile(r"[^a-zA-Z0-9\s]")


def clean_text(text: str, lang: str = "pt-br") -> str:
    text = _TOKEN_PATTERN.sub("'", text)
    if lang == "pt-br":
        text = _STRIP_PATTERN_PT.sub(" ", text.lower())
    else:
        text = _STRIP_PATTERN_EN.sub(" ", text.lower())

    stop = load_stopwords(
        include_pt=(lang == "pt-br"),
        include_en=True,
    )
    tokens = [t for t in text.split() if t not in stop and len(t) > 1]
    return " ".join(tokens)


def tokenize(text: str, lang: str = "pt-br") -> list[str]:
    return clean_text(text, lang).split()


def extract_clean_text(text: str, lang: str = "pt-br") -> str:
    return clean_text(text, lang)
