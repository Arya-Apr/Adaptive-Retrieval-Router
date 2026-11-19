import hashlib
import re
from .models import RetrievalDecision, Route

FRESH = re.compile(r"\b(today|yesterday|this morning|recently|latest|just discussed|what did .+ say|what happened)\b", re.I)
STATIC = re.compile(r"\b(documentation|architecture|design|specification|pdf|document|policy|manual)\b", re.I)


def normalize(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def cache_key(query: str) -> str:
    # Versioned, normalized exact-intent key; TTL prevents stale source/freshness assumptions.
    return "route:v1:" + hashlib.sha256(normalize(query).encode()).hexdigest()


class ReasoningEngine:
    """Heuristics are decisive only for clear cases; ambiguous cases are safe defaults in Phase 1."""
    def decide(self, query: str) -> RetrievalDecision:
        live, docs = bool(FRESH.search(query)), bool(STATIC.search(query))
        if live and docs:
            route, rag, mcp, confidence = Route.HYBRID, ["drive"], ["slack"], .93
        elif live:
            route, rag, mcp, confidence = Route.MCP, [], ["slack"], .88
        elif docs:
            route, rag, mcp, confidence = Route.RAG, ["drive"], [], .88
        else:
            # Phase 1 conservative default. Phase 2 replaces this branch with validated Ollama JSON.
            route, rag, mcp, confidence = Route.RAG, ["drive"], [], .55
        return RetrievalDecision(route=route, rag_sources=rag, mcp_sources=mcp,
                                 query=query, freshness_required=live, confidence=confidence,
                                 reasoning="deterministic freshness/static-document signals")


class AzureRouter:
    live = re.compile(r"\b(latest|current(?:ly)?|today|recent\w*|newest|now|learn|release notes|this (?:week|month)|supported regions|pricing)\b", re.I)
    local = re.compile(r"\b(python|sdk|installed|local|signature|method|class|offline)\b", re.I)

    def decide(self, query: str) -> RetrievalDecision:
        fresh = bool(self.live.search(query))
        indexed = bool(self.local.search(query))
        route = Route.HYBRID if fresh and indexed else Route.MCP if fresh else Route.RAG
        if normalize(query).strip("!.?") in {"hi", "hello", "thanks", "thank you"}:
            route = Route.NONE
        return RetrievalDecision(route=route, query=query, freshness_required=fresh,
            rag_sources=["azure-sdk"] if route in (Route.RAG, Route.HYBRID) else [],
            mcp_sources=["microsoft-learn"] if fresh else [], confidence=.85 if fresh or indexed else .55,
            reasoning={Route.NONE:"Greeting or acknowledgement", Route.RAG:"Search installed SDK reference",
                Route.MCP:"Requested current Microsoft guidance", Route.HYBRID:"Compare installed SDK and current guidance"}[route])
