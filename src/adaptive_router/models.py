from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class Route(StrEnum):
    NONE = "NONE"
    RAG = "RAG"
    MCP = "MCP"
    HYBRID = "HYBRID"


class RetrievalDecision(BaseModel):
    route: Route
    rag_sources: list[str] = Field(default_factory=list)
    mcp_sources: list[str] = Field(default_factory=list)
    query: str
    freshness_required: bool
    confidence: float = Field(ge=0, le=1)
    reasoning: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    user_id: str = Field(min_length=1)


class SearchResult(BaseModel):
    document_id: str
    title: str
    source: str
    url: str | None = None
    snippet: str
    score: float
    retrieval_method: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    request_id: str
    decision: RetrievalDecision
    cache_hit: bool
    retrieval_confidence: float = Field(ge=0, le=1)
    results: list[SearchResult]
