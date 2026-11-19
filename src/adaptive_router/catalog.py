"""Build a searchable snapshot of the public API reference shipped with Azure SDKs."""
import asyncio
import inspect
import re
import sqlite3
from contextlib import closing
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

from .models import SearchResult

PACKAGES = {"azure.identity": "azure-identity", "azure.storage.blob": "azure-storage-blob"}
STOP = set("a an the to for in of on how what which is do i and or with me show find azure sdk microsoft python reference latest currently".split())
SEARCH = """
SELECT symbol, url, snippet(reference, 1, '', '', ' … ', 32), package, release,
       bm25(reference, 6, 1, 0, 0, 0, 6) AS distance
FROM reference WHERE reference MATCH ? ORDER BY distance, symbol LIMIT 10
"""


def entries():
    for namespace, package in PACKAGES.items():
        module = import_module(namespace)
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if name.startswith("_") or not cls.__module__.startswith(namespace):
                continue
            members = [(None, cls), *inspect.getmembers(cls, inspect.isfunction)]
            for method, member in members:
                if method and method.startswith("_"):
                    continue
                body = inspect.getdoc(member)
                if not body:
                    continue
                symbol = f"{name}.{method}" if method else name
                base = f"https://learn.microsoft.com/en-us/python/api/{package}/{namespace}.{name.lower()}?view=azure-python"
                url = base if not method else base + "#" + f"{namespace}.{name}.{method}".lower().replace(".", "-").replace("_", "-")
                name_terms = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", symbol).replace("_", " ")
                yield symbol, body, url, package, version(package), name_terms


class Catalog:
    def __init__(self, path: Path = Path(".arr/azure.sqlite3")):
        self.path = path

    def build(self) -> int:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DROP TABLE IF EXISTS reference")
            db.execute("CREATE VIRTUAL TABLE reference USING fts5(symbol, body, url UNINDEXED, package UNINDEXED, release UNINDEXED, name_terms, tokenize='porter unicode61')")
            db.executemany("INSERT INTO reference VALUES(?,?,?,?,?,?)", entries())
            count, unique_count = db.execute("SELECT count(*), count(DISTINCT url) FROM reference").fetchone()
            if not count or unique_count != count:
                raise ValueError("Azure reference index failed citation uniqueness validation")
            return count

    def lookup(self, query: str) -> list[SearchResult]:
        words = [w for w in dict.fromkeys(re.findall(r"[a-z0-9]+", query.lower())) if w not in STOP][:40]
        if not words:
            return []
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(SEARCH, (" OR ".join(f'"{word}"' for word in words),)).fetchall()
        return [SearchResult(document_id=url, title=name, url=url, source="azure-sdk",
                             snippet=snippet, score=1/rank, retrieval_method="bm25",
                             metadata={"package": package, "version": release, "bm25": -distance})
                for rank, (name, url, snippet, package, release, distance) in enumerate(rows, 1)]

    async def search(self, query: str, sources: list[str], user_id: str):
        return await asyncio.to_thread(self.lookup, query) if "azure-sdk" in sources else []
