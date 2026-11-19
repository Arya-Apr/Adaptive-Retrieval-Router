# Adaptive Retrieval Router

Atlas is a Next.js search interface for Azure Python developers. A FastAPI endpoint runs one LangGraph workflow. Questions about installed APIs search a local index. Questions requesting current guidance use Microsoft's public Learn MCP server. Hybrid questions retrieve from both and return up to ten citations. A live-source outage leaves indexed results available with a warning.

## Run locally

Use Python 3.12, uv, and Node 24. From the repository root in PowerShell:

```powershell
uv venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e '.[dev]'
.\.venv\Scripts\python -m uvicorn adaptive_router.main:app --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run build
npm run start -- --hostname 127.0.0.1 --port 3000
```

Open http://127.0.0.1:3000. Try **Compare Python upload_blob with current Azure storage guidance**. The source labels distinguish installed SDK symbols from live citations. Live and hybrid searches send the query text to Microsoft's public endpoint. Use public technical questions. Local searches work offline after installation. Set `REDIS_URL` to enable route caching. The default local launch requires no database service.

## SQL and retrieval

On startup, the API rebuilds a SQLite FTS5 index from the installed Azure Identity and Blob Storage packages. Each entry contains its API symbol, docstring, package version and Microsoft Learn citation. One transaction replaces the index and validates row count and citation uniqueness before commit. Parameterized MATCH queries use stemming, weighted BM25 ranking and SQL snippet extraction. The active backend is SQLite. The earlier PostgreSQL/pgvector schema remains in `db/init.sql`.

The live adapter initializes an MCP session, discovers the search tool and accepts HTTPS citations from learn.microsoft.com. Within each source, results retain their native rank. The merge uses reciprocal rank to interleave results and deduplicates by URL. The confidence field is a heuristic. All sources contain public documentation.

## Reproduce the evaluation

```powershell
.\.venv\Scripts\python evaluation/run.py
.\.venv\Scripts\python -m pytest -q
```

The runner scores exact route matches on 28 hand-labeled questions against an always-RAG baseline. Twelve of the questions also have a single target SDK symbol. For those it measures hit rate at five and mean reciprocal rank at ten using the same index and tokenizer for both systems. The baseline searches symbol names, including split CamelCase names. The full system also searches docstrings. Each miss contributes zero. See `evaluation/results.json` for every query, expected label, prediction and rank. This is a small developer-authored benchmark. It measures local retrieval quality and routing. Live result relevance, Redis latency and Azure deployment are outside its scope.
