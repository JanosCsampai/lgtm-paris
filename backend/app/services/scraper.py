import asyncio
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.db import get_db

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; price-scraper/1.0)",
    "Accept-Language": "en-GB,en;q=0.9",
}
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "noscript", "svg"]
SKIP_SUBSTRINGS = [
    "blog", "news", "about", "contact", "privacy", "terms",
    "login", "cart", "facebook", "instagram", ".pdf",
]
PRICE_RE = re.compile(r"([£€$])\s*([0-9]{1,6})(?:[.,]([0-9]{1,2}))?")
TOP_LINKS = 3
TOP_SUBLINKS = 2


def _currency_from_symbol(sym: str) -> str:
    return {"€": "EUR", "£": "GBP", "$": "USD"}.get(sym, "")


def _tokenize_query(q: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", q.lower()) if len(t) > 1]


def _build_phrases(tokens: list[str]) -> list[str]:
    phrases: list[str] = []
    for i in range(len(tokens) - 2):
        phrases.append(f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}")
    for i in range(len(tokens) - 1):
        phrases.append(f"{tokens[i]} {tokens[i+1]}")
    return sorted(set(phrases), key=lambda x: -len(x))


def _phrase_present(text_lower: str, phrase: str) -> bool:
    parts = phrase.split()
    pat = r"\b" + r"[\s\-]+".join(map(re.escape, parts)) + r"\b"
    return re.search(pat, text_lower) is not None


def _parse_price(m: re.Match) -> tuple[str, float]:
    sym = m.group(1)
    whole = m.group(2)
    frac = m.group(3) or "0"
    return sym, float(f"{whole}.{frac}")


def _same_site(u: str, host: str) -> bool:
    netloc = urlparse(u).netloc.lower()
    h = host.lower()
    if not netloc:
        return False
    if h.endswith("co.uk"):
        suffix = ".".join(h.split(".")[-3:])
    else:
        suffix = ".".join(h.split(".")[-2:])
    return netloc == h or netloc == suffix or netloc.endswith("." + suffix)


def _should_skip(u: str) -> bool:
    path = (urlparse(u).path or "").lower()
    return any(x in path for x in SKIP_SUBSTRINGS)


def _score_url(u: str, tokens: list[str]) -> int:
    path = (urlparse(u).path or "").lower()
    words = [w for w in re.split(r"[^a-z0-9]+", path) if w]
    tset = set(tokens)
    overlap = sum(1 for w in words if w in tset)
    extra = sum(1 for w in words if w not in tset)
    return overlap * 10 - extra


def _extract_links(page_url: str, html: str, host: str, tokens: list[str]) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    out: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(page_url, a["href"].strip())
        if not _same_site(full, host):
            continue
        if full in seen or _should_skip(full):
            continue
        seen.add(full)
        out.append(full)
    out.sort(key=lambda u: _score_url(u, tokens), reverse=True)
    return out


def _find_price_in_html(html: str, tokens: list[str]) -> tuple[str, float] | None:
    soup = BeautifulSoup(html, "lxml")
    for t in soup(NOISE_TAGS):
        t.decompose()
    phrases = _build_phrases(tokens)
    top_phrases = phrases[:3]

    def container_matches(text_lower: str) -> bool:
        if tokens and not all(t in text_lower for t in tokens):
            return False
        if top_phrases and not any(_phrase_present(text_lower, p) for p in top_phrases):
            return False
        return True

    for node in soup.find_all(string=lambda s: s and any(c in s for c in "£€$")):
        raw = str(node)
        m = PRICE_RE.search(raw)
        if not m:
            continue
        sym, val = _parse_price(m)
        if val == 0.0:
            continue
        cur = node.parent
        for _ in range(12):
            if cur is None:
                break
            if cur.name in ("div", "li", "article", "section", "main", "body"):
                ctx = cur.get_text(" ", strip=True).lower()
                if container_matches(ctx):
                    return sym, round(val, 2)
            cur = cur.parent

    return None


def _fast_hit(html: str, tokens: list[str]) -> tuple[str, float] | None:
    if not any(c in html for c in "£€$"):
        return None
    low = html.lower()
    if tokens and not all(t in low for t in tokens):
        return None
    return _find_price_in_html(html, tokens)


def _scrape_sync(website: str, query: str) -> dict | None:
    """Synchronous multi-level crawl of a single website looking for a price.

    Returns a dict with price info or None.
    """
    tokens = _tokenize_query(query)
    start = website.rstrip("/")
    host = urlparse(start).netloc

    timeout = httpx.Timeout(connect=4.0, read=8.0, write=4.0, pool=4.0)
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10, keepalive_expiry=10)

    try:
        with httpx.Client(
            timeout=timeout, limits=limits, headers=HEADERS,
            follow_redirects=True, verify=True,
        ) as c:
            home_html = c.get(start).text
            hit = _fast_hit(home_html, tokens)
            if hit:
                return {"page_url": start, "symbol": hit[0], "price": hit[1]}

            lvl1 = _extract_links(start, home_html, host, tokens)[:TOP_LINKS]
            for u1 in lvl1:
                try:
                    html1 = c.get(u1).text
                except httpx.HTTPError:
                    continue
                hit = _fast_hit(html1, tokens)
                if hit:
                    return {"page_url": u1, "symbol": hit[0], "price": hit[1]}

                lvl2 = _extract_links(u1, html1, host, tokens)[:TOP_SUBLINKS]
                for u2 in lvl2:
                    try:
                        html2 = c.get(u2).text
                    except httpx.HTTPError:
                        continue
                    hit = _fast_hit(html2, tokens)
                    if hit:
                        return {"page_url": u2, "symbol": hit[0], "price": hit[1]}
    except Exception:
        logger.debug("Scrape failed for %s", website, exc_info=True)

    return None


async def scrape_provider_price(
    website: str,
    query: str,
) -> dict | None:
    """Async wrapper — runs the blocking crawl in a thread pool."""
    return await asyncio.to_thread(_scrape_sync, website, query)


async def scrape_and_store_prices(
    providers: list[dict],
    query: str,
    service_type_slug: str,
) -> dict[str, dict]:
    """Scrape prices for multiple providers concurrently and store as observations.

    Args:
        providers: list of dicts with at least ``_id``, ``name``, ``website``,
                   and ``location`` keys (as returned by a MongoDB query).
        query: the user's search query (used to match prices on websites).
        service_type_slug: the slug to associate observations with.

    Returns:
        Mapping of provider_id (str) -> observation dict for providers
        where a price was found.
    """
    scrapable = [p for p in providers if p.get("website")]
    if not scrapable:
        return {}

    logger.info(
        "Scraping prices for %d/%d providers (query=%r)",
        len(scrapable), len(providers), query,
    )

    tasks = [
        scrape_provider_price(p["website"], query)
        for p in scrapable
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    db = get_db()
    observations: dict[str, dict] = {}

    for provider, result in zip(scrapable, results):
        if isinstance(result, Exception) or result is None:
            continue

        pid = provider["_id"]
        currency = _currency_from_symbol(result["symbol"])
        now = datetime.now(timezone.utc)

        obs_doc = {
            "provider_id": pid,
            "service_type": service_type_slug,
            "category": service_type_slug,
            "price": result["price"],
            "currency": currency,
            "source_type": "scrape",
            "source_url": result["page_url"],
            "location": provider["location"],
            "observed_at": now,
            "created_at": now,
        }
        try:
            await db.observations.insert_one(obs_doc)
            observations[str(pid)] = obs_doc
            logger.info(
                "Stored scraped price %s%.2f for %s from %s",
                result["symbol"], result["price"],
                provider["name"], result["page_url"],
            )
        except Exception:
            logger.warning(
                "Failed to store observation for %s", provider["name"],
                exc_info=True,
            )

    logger.info(
        "Scraping complete: %d/%d providers returned prices",
        len(observations), len(scrapable),
    )
    return observations
