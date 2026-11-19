# Adaptive Retrieval Router

Azure Python developers often need to answer two different questions in the same search: what their installed SDK supports and what Microsoft recommends today. Atlas uses a Next.js interface and a single FastAPI/LangGraph workflow to choose where to look.

| Decision | What the router does | Example query |
|---|---|---|
| `NONE` | Skips retrieval for a recognized greeting or acknowledgement. | “Thanks!” |
| `RAG` | Searches the installed Azure SDK reference index. | “Read container metadata and properties.” |
| `MCP` | Searches current documentation through the public Microsoft Learn MCP server. | “What is the latest Azure storage pricing?” |
| `HYBRID` | Searches both sources and merges up to ten citations. | “Compare my installed identity client with the latest guidance.” |

If Microsoft Learn is unavailable during a hybrid search, Atlas returns the indexed matches with a warning.

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

## Evaluation results

The developer-authored benchmark contains 28 hand-labeled routing queries. Twelve of those queries also specify a target SDK symbol in the 256-entry index.

| Metric | Queries | Atlas | Baseline |
|---|---:|---:|---|
| Correct routing decision | 28 | 24/28 (85.7%) | 12/28 (42.9%), always choose RAG |
| Target SDK symbol in the top 5 | 12 | 9/12 (75.0%) | 7/12 (58.3%), title-only BM25 |
| Mean reciprocal rank at 10 | 12 | 0.438 | 0.383, title-only BM25 |

Both retrieval runs use the same tokenizer. The baseline searches symbol names, including split CamelCase names. Atlas also searches docstrings. Reciprocal rank gives a first-place target 1 point, a second-place target ½ point, and a target outside the top ten zero. The [per-query results](evaluation/results.json) record each route prediction and target rank.

### Where it failed

- **Release freshness.** “Are there new features in the November release?” went to `RAG`. The router missed the reference to a dated release and skipped the expected live lookup.
- **Two-source comparison.** “Compare DefaultAzureCredential with the newest authentication guidance” went to `MCP`. The freshness cue triggered live search, but the class name alone did not trigger the SDK lookup needed for `HYBRID`.
- **Method ranking.** “Download a blob into a stream” routed correctly to `RAG`, but full-text BM25 missed `BlobClient.download_blob` in the top ten. The title-only baseline placed it tenth.

### Reproduce the evaluation

```powershell
.\.venv\Scripts\python evaluation/run.py
.\.venv\Scripts\python -m pytest -q
```
