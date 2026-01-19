from dataclasses import dataclass, field
from typing import List, Set, Dict
import re

STOPWORDS = {
    "the", "and", "or", "of", "in", "a", "to", "for", "on", "with", "that",
    "is", "are", "was", "were", "it", "this", "as", "at", "by", "from",
    "an", "be", "have", "has", "had", "but", "not", "your", "you", "i",
    "we", "they", "their", "them", "our", "us", "will", "would", "can",
    "could", "should", "may", "might", "also", "about", "into", "than",
    "more", "most", "some", "any", "all", "just", "like", "if", "so",
    "no", "yes", "do", "does", "did", "because", "when", "what", "who",
    "which", "how", "why", "where", "while", "over", "under", "up", "down",
    "out", "new", "old", "news", "ai"
}

DEFAULT_EXCLUDE_KEYWORDS = {"productivity", "funding", "grant", "labor", "startup", "venture"}


@dataclass
class TopicSignature:
    theme: str
    angles: List[str]
    entities: Set[str] = field(default_factory=set)
    keywords: Set[str] = field(default_factory=set)
    exclude_keywords: Set[str] = field(default_factory=set)
    section_keywords: Dict[str, Set[str]] = field(default_factory=dict)


def _tokens(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text or "")


def _is_entity(tok: str) -> bool:
    # Exclude overly generic terms that appear everywhere in AI context
    generic_terms = {"AI", "Tech", "Data", "Model", "Models", "System", "Systems"}
    if tok in generic_terms:
        return False
    return tok.istitle() or tok.isupper() or tok in {"Grok", "X", "Elon", "Musk", "deepfake", "deepfakes"}


def _keywordize(text: str) -> Set[str]:
    kws = set()
    for t in _tokens(text.lower()):
        if len(t) >= 4 and t not in STOPWORDS:
            kws.add(t)
    return kws


def build_topic_signature(plan, anchored_outline: dict, provided_sources: list, facts: list) -> TopicSignature:
    theme = getattr(plan, "theme", "") or ""
    angles = getattr(plan, "angle_choices", [])[:2]
    text_bundle = " ".join([theme] + angles)

    entities = set(t for t in _tokens(text_bundle) if _is_entity(t))
    keywords = _keywordize(text_bundle)

    section_keywords = {}
    try:
        for sec in anchored_outline.get("sections", []):
            sid = sec.get("section_id") or sec.get("id") or ""
            sec_text = " ".join(b.get("text", "") for b in sec.get("bullets", []))
            if sid:
                section_keywords[sid] = _keywordize(sec_text)
    except Exception:
        pass

    # Exclude generic drift terms unless they are in theme/angles
    exclude_keywords = set(DEFAULT_EXCLUDE_KEYWORDS)
    for ex in list(exclude_keywords):
        if ex in keywords:
            exclude_keywords.discard(ex)

    # Include entities from provided sources titles
    for src in provided_sources or []:
        title = src.get("title", "")
        entities.update(t for t in _tokens(title) if _is_entity(t))
        keywords.update(_keywordize(title))

    # Facts keywords
    for f in facts or []:
        txt = f.get("text", "") or f.get("fact_text", "")
        keywords.update(_keywordize(txt))

    return TopicSignature(
        theme=theme,
        angles=angles,
        entities=entities,
        keywords=keywords,
        exclude_keywords=exclude_keywords,
        section_keywords=section_keywords
    )
