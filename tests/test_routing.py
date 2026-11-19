from adaptive_router.models import Route
from adaptive_router.routing import ReasoningEngine


def test_hybrid_request_routes_to_both_layers():
    d = ReasoningEngine().decide("What did Sarah discuss about the payment migration yesterday, and is there a design document?")
    assert d.route == Route.HYBRID
    assert d.mcp_sources == ["slack"]
    assert d.rag_sources == ["drive"]


def test_design_document_routes_to_rag():
    assert ReasoningEngine().decide("Find architecture documentation").route == Route.RAG
