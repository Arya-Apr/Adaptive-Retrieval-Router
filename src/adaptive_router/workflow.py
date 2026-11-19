from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from .models import RetrievalDecision, SearchResult
from .routing import ReasoningEngine
from .learn import LearnUnavailable
from .services import McpRegistry, PermissionChecker, RagService, merge_top_ten, retrieval_confidence


class State(TypedDict, total=False):
    query: str
    user_id: str
    decision: RetrievalDecision
    results: list[SearchResult]
    retrieval_confidence: float
    warnings: list[str]


def build_workflow(reasoner: ReasoningEngine, rag: RagService, mcp: McpRegistry, permissions: PermissionChecker):
    async def route(state: State): return {"decision": state.get("decision") or reasoner.decide(state["query"])}
    async def retrieve(state: State):
        d = state["decision"]
        rag_sources = await permissions.allowed_sources(state["user_id"], d.rag_sources)
        mcp_sources = await permissions.allowed_sources(state["user_id"], d.mcp_sources)
        results = await rag.search(d.query, rag_sources, state["user_id"])
        warnings = []
        try:
            results += await mcp.search(d.query, mcp_sources, state["user_id"])
        except LearnUnavailable:
            warnings.append("Microsoft Learn is unavailable. Live results could not be retrieved.")
        merged = merge_top_ten(results)
        return {"results": merged, "warnings": warnings, "retrieval_confidence": retrieval_confidence(merged, rag_sources + mcp_sources)}
    graph = StateGraph(State)
    graph.add_node("route", route); graph.add_node("retrieve", retrieve)
    graph.add_edge(START, "route"); graph.add_edge("route", "retrieve"); graph.add_edge("retrieve", END)
    return graph.compile()
