from typing import List, Dict, Optional
from topic_signature import TopicSignature, _keywordize


def score_source_relevance(source_text: str, topic: TopicSignature, section_id: Optional[str] = None) -> float:
    if not source_text:
        return -10.0
    txt = source_text.lower()
    score = 0.0

    # entities
    for ent in topic.entities:
        if ent.lower() in txt:
            score += 3

    # keywords
    kw_hits = sum(1 for kw in topic.keywords if kw in txt)
    score += min(kw_hits, 5)

    # section keywords
    if section_id and section_id in topic.section_keywords:
        sec_hits = sum(1 for kw in topic.section_keywords[section_id] if kw in txt)
        score += min(sec_hits, 4)

    # exclude
    ex_hits = sum(1 for ex in topic.exclude_keywords if ex in txt)
    score -= min(ex_hits * 2, 6)

    return score


def filter_editorial_sources_by_topic(
    sources: List[Dict],
    topic: TopicSignature,
    section_id: Optional[str] = None,
    min_score: float = 3.0,  # Increased from 2.0 for stricter filtering
    allow_provided: bool = True
) -> List[Dict]:
    filtered = []
    for src in sources:
        if src.get("source_type") == "provided_source" and allow_provided:
            filtered.append(src)
            continue
        text = " ".join([
            src.get("title", ""),
            src.get("summary", ""),
            src.get("text", ""),
        ])
        sc = score_source_relevance(text, topic, section_id)
        if sc >= min_score:
            filtered.append(src)
    return filtered
