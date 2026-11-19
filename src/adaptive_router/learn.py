import asyncio
import json
from urllib.parse import urlparse

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .models import SearchResult

ENDPOINT = "https://learn.microsoft.com/api/mcp"
TOOL = "microsoft_docs_search"


class LearnUnavailable(Exception):
    pass


class Learn:
    async def search(self, query: str, sources: list[str], user_id: str):
        if "microsoft-learn" not in sources:
            return []
        try:
            async with asyncio.timeout(18), streamablehttp_client(ENDPOINT) as (reader, writer, _):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    available = await session.list_tools()
                    if TOOL not in {t.name for t in available.tools}:
                        raise ValueError("Search unavailable")
                    result = await session.call_tool(TOOL, {"query": query})
                    if result.isError:
                        raise ValueError("Search failed")
                    rows = []
                    for part in result.content:
                        if part.type == "text":
                            payload = json.loads(part.text)
                            rows.extend(payload if isinstance(payload, list) else payload.get("results", [payload]))
                    hits = []
                    for row in rows[:10]:
                        url = row.get("contentUrl") or row.get("url", "")
                        if urlparse(url).hostname == "learn.microsoft.com" and url.startswith("https://"):
                            hits.append(SearchResult(document_id=url, url=url, title=row["title"], snippet=row.get("content","")[:480],
                                source="microsoft-learn", score=1/(len(hits)+1), retrieval_method="mcp", metadata={"tool": TOOL}))
                    if rows and not hits:
                        raise ValueError("Unrecognized citation format")
                    return hits
        except Exception as exc:
            raise LearnUnavailable from exc
