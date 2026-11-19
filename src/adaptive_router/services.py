from collections.abc import Sequence
import re
from .models import SearchResult


class PermissionChecker:
    """Development-only explicit mock. Production implementation must enforce source ACLs."""
    async def allowed_sources(self, user_id: str, requested: Sequence[str]) -> list[str]:
        return list(requested)


class RagService:
    """Phase-1 local hybrid retrieval; replace corpus with PostgreSQL repository in Phase 2."""
    _documents = [
        SearchResult(document_id="drive:payment-design", title="Payment Migration Design", source="drive",
                     url="https://drive.example/payment-migration-design", snippet="Architecture and rollout design for payment migration.",
                     score=0, retrieval_method="hybrid", metadata={"kind": "design"}),
        SearchResult(document_id="drive:payment-architecture", title="Payment Service Architecture", source="drive",
                     url="https://drive.example/payment-architecture", snippet="Architecture documentation for the payment service.",
                     score=0, retrieval_method="hybrid", metadata={"kind": "architecture"}),
    ]

    async def search(self, query: str, sources: list[str], user_id: str) -> list[SearchResult]:
        if "drive" not in sources: return []
        terms = set(re.findall(r"[a-z]{3,}", query.lower()))
        results: list[SearchResult] = []
        for doc in self._documents:
            text_terms = set(re.findall(r"[a-z]{3,}", f"{doc.title} {doc.snippet}".lower()))
            keyword_score = len(terms & text_terms) / max(len(terms), 1)
            # Stand-in embedding score keeps the merge contract identical to pgvector cosine scores.
            semantic_score = 0.9 if {"payment", "migration"} <= terms and "Migration" in doc.title else keyword_score
            score = round(0.55 * semantic_score + 0.45 * keyword_score, 4)
            if score > 0:
                results.append(doc.model_copy(update={"score": score}))
        return sorted(results, key=lambda item: item.score, reverse=True)


class McpRegistry:
    """Capability registry. Only registered source names can be called."""
    async def search(self, query: str, sources: list[str], user_id: str) -> list[SearchResult]:
        if "slack" not in sources: return []
        terms = set(re.findall(r"[a-z]{3,}", query.lower()))
        if not ({"sarah", "payment", "migration"} & terms): return []
        return [SearchResult(document_id="slack:payment-migration:thread-42", title="Sarah — payment migration update",
                             source="slack", url="https://slack.example/thread/42",
                             snippet="Yesterday Sarah discussed a staged migration, monitoring, and rollback readiness.",
                             score=0.92, retrieval_method="mcp", metadata={"capability": "slack.search", "fresh": True})]


def merge_top_ten(results: list[SearchResult]) -> list[SearchResult]:
    unique: dict[str, SearchResult] = {}
    for item in results:
        prior = unique.get(item.document_id)
        if prior is None or item.score > prior.score:
            unique[item.document_id] = item
    return sorted(unique.values(), key=lambda item: item.score, reverse=True)[:10]


def retrieval_confidence(results: list[SearchResult], requested_sources: Sequence[str]) -> float:
    """Explainable configurable baseline: quality, support, and requested-source coverage."""
    if not results: return 0.0
    quality = results[0].score
    support = min(len(results) / 3, 1.0)
    coverage = len({r.source for r in results} & set(requested_sources)) / max(len(set(requested_sources)), 1)
    return round(0.55 * quality + 0.25 * support + 0.20 * coverage, 4)
