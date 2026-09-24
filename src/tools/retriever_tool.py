import math
import re
from collections import Counter
from typing import Any, Dict, List
from langchain_core.tools import tool
from src.config import settings

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below", "from",
    "up", "down", "of", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can",
    "will", "just", "should", "now", "what", "which", "who", "whom", "this",
    "that", "these", "those", "am", "have", "has", "had", "do", "does", "did",
    "and", "but", "if", "or", "because", "as", "until", "while", "my", "your", "by",
}


def _stem(word: str) -> str:
    if len(word) <= 3:
        return word
    for suffix in ("ations", "ation", "ings", "ing", "ed", "ies", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            if suffix == "ies":
                return word[:-3] + "y"
            return word[: -len(suffix)]
    return word


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [
        _stem(t)
        for t in tokens
        if t not in STOPWORDS and (len(t) > 1 or t.isdigit())
    ]


@tool
def search_knowledge_base(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search the knowledge_base.txt file using English keywords and return top relevant snippets with match details."""
    kb_path = settings.knowledge_base_path
    if not kb_path.exists():
        return [{"snippet": f"Error: Knowledge base file not found at {kb_path}", "score": 0.0, "matched_keywords": []}]

    raw_text = kb_path.read_text(encoding="utf-8").strip()
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", raw_text) if chunk.strip()]
    if not chunks:
        return []

    raw_query_words = [
        w for w in re.findall(r"[a-z0-9]+", query.lower())
        if w not in STOPWORDS and (len(w) > 1 or w.isdigit())
    ]
    stem_to_original = {_stem(w): w for w in raw_query_words}
    query_tokens = list(dict.fromkeys(_stem(w) for w in raw_query_words))

    if not query_tokens:
        return [
            {"snippet": chunk, "score": 0.0, "matched_keywords": [], "query": query}
            for chunk in chunks[:top_k]
        ]

    tokenized_chunks = [_tokenize(chunk) for chunk in chunks]
    header_tokens_list = [_tokenize(chunk.splitlines()[0]) for chunk in chunks]
    num_chunks = len(chunks)

    idf = {}
    for token in query_tokens:
        doc_freq = sum(1 for tokens in tokenized_chunks if token in tokens)
        idf[token] = math.log((num_chunks + 1) / (doc_freq + 1)) + 1.0

    scored_chunks = []
    for idx, (chunk, tokens, header_tokens) in enumerate(
        zip(chunks, tokenized_chunks, header_tokens_list)
    ):
        if not tokens:
            continue
        counts = Counter(tokens)
        header_set = set(header_tokens)
        score = 0.0
        matched_keywords = []

        for t in query_tokens:
            if t in counts:
                tf = counts[t] / len(tokens)
                header_boost = 2.5 if t in header_set else 1.0
                score += tf * idf[t] * header_boost
                label = stem_to_original.get(t, t)
                if t in header_set:
                    label = f"{label} (header)"
                matched_keywords.append(label)

        if score > 0:
            scored_chunks.append(
                {
                    "snippet": chunk,
                    "score": round(score, 4),
                    "matched_keywords": matched_keywords,
                    "query": query,
                }
            )

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)
    return scored_chunks[:top_k]
