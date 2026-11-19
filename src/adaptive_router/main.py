import uuid
import asyncio
from contextlib import asynccontextmanager
from .catalog import Catalog
from .learn import Learn
from fastapi import FastAPI
from .cache import RouteCache
from .models import SearchRequest, SearchResponse
from .routing import AzureRouter, cache_key
from .services import McpRegistry, PermissionChecker, RagService
from .workflow import build_workflow

catalog = Catalog()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.entries = await asyncio.to_thread(catalog.build)
    yield
    if route_cache.redis:
        await route_cache.redis.aclose()

app = FastAPI(title="Adaptive Retrieval Router", version="0.2.0", lifespan=lifespan)
workflow = build_workflow(AzureRouter(), catalog, Learn(), PermissionChecker())
route_cache = RouteCache()


@app.get("/health")
async def health(): return {"status": "ok", "indexed_entries": app.state.entries}


@app.post("/v1/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    key = "azure-v2:" + cache_key(request.query)
    cached = await route_cache.get(key)
    inputs = {"query": request.query, "user_id": request.user_id}
    if cached:
        inputs["decision"] = cached.model_copy(update={"query": request.query})
    state = await workflow.ainvoke(inputs)
    decision = state["decision"]
    if not cached: await route_cache.set(key, decision)
    return SearchResponse(request_id=str(uuid.uuid4()), decision=decision,
                          cache_hit=cached is not None, warnings=state["warnings"], retrieval_confidence=state["retrieval_confidence"], results=state["results"])
