"""Online audit of published SDK pages and method anchors. Run from the repo root."""
import asyncio
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urldefrag

import httpx

from adaptive_router.catalog import entries


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.ids.add(dict(attrs).get("id"))


async def main():
    pages = defaultdict(list)
    for symbol, _, url, *_ in entries():
        page, anchor = urldefrag(url)
        pages[page].append((symbol, anchor))
    failures = []
    limit = asyncio.Semaphore(5)
    async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
        async def check(page, targets):
            async with limit:
                response = await client.get(page)
            if response.status_code != 200:
                failures.append(f"{response.status_code} {page}")
                return
            anchors = Anchors()
            anchors.feed(response.text)
            failures.extend(f"{symbol}: missing #{anchor}" for symbol, anchor in targets
                            if anchor and anchor not in anchors.ids)
        await asyncio.gather(*(check(page, targets) for page, targets in pages.items()))
    print(f"{sum(map(len, pages.values()))} citations across {len(pages)} pages")
    if failures:
        raise SystemExit("\n".join(sorted(failures)))


if __name__ == "__main__":
    asyncio.run(main())
