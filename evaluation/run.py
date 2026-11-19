"""Run from repository root. Output per-case ranks and macro-independent totals."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from adaptive_router.catalog import Catalog, SEARCH, STOP
from adaptive_router.routing import AzureRouter
import re

folder = Path(__file__).parent
cases = json.loads((folder / "cases.json").read_text())
catalog = Catalog()
size = catalog.build()
results = []
with closing(sqlite3.connect(catalog.path)) as db:
    for expected, query, *target in cases:
        predicted = AzureRouter().decide(query).route.value
        row = dict(query=query, expected=expected, predicted=predicted)
        if target:
            ranked = [hit.title for hit in catalog.lookup(query)]
            words = [w for w in dict.fromkeys(re.findall(r"[a-z0-9]+", query.lower())) if w not in STOP]
            title_query = "{symbol name_terms} : (" + " OR ".join(f'"{w}"' for w in words) + ")"
            titles = [r[0] for r in db.execute(SEARCH, (title_query,))]
            row.update(target=target[0], full_rank=ranked.index(target[0])+1 if target[0] in ranked else None,
                       title_rank=titles.index(target[0])+1 if target[0] in titles else None)
        results.append(row)
local = [r for r in results if "target" in r]
summary = dict(entries=size, routing_queries=len(results), routing_correct=sum(r["expected"]==r["predicted"] for r in results),
               always_rag_correct=sum(r["expected"]=="RAG" for r in results), retrieval_queries=len(local))
for method in ("full_rank","title_rank"):
    summary[method+"_hit_at_5"] = sum(0 < (r[method] or 100) <= 5 for r in local)
    summary[method+"_mrr_at_10"] = round(sum(1/r[method] for r in local if r[method])/len(local), 3)
(folder/"results.json").write_text(json.dumps(dict(summary=summary, cases=results), indent=2)+"\n")
print(summary)
