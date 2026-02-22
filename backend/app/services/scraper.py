import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

from app.config import settings
from app.db import get_db

try:
    from linkup import LinkupClient
except ImportError:
    LinkupClient = None

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
PRICE_PAGE_KEYWORDS = {
    "price", "pricing", "prices", "cost", "costs", "rate", "rates",
    "fee", "fees", "tariff", "tariffs", "labor", "labour", "service",
    "services", "repair", "repairs", "quote", "menu",
}
MAX_LLM_TEXT = 8_000
MIN_OVERLAP_FOR_LLM = 2
MIN_OVERLAP_FOR_LINKUP = 2

_PRICE_EXTRACT_PROMPT = """\
You are a price extraction assistant. Given text scraped from a local service \
provider's website, extract the price for the specified service.

Rules:
- Return ONLY a JSON object: {"price": <number>, "currency_symbol": "<symbol>"}
- The currency_symbol must be one of: £, €, $
- Match SEMANTICALLY, not just literally. For example:
  "chain replacement" matches "chain fitting", "new chain", "chain install".
  "oil change" matches "oil & filter change", "engine oil service".
  "screen repair" matches "screen replacement", "display fix".
- If multiple prices match, return the most specific one for the query.
- If you truly cannot find any price related to the requested service, return: {"price": null}
- Do NOT guess or estimate — only extract prices explicitly stated on the page.\
"""


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
    price_bonus = 15 if PRICE_PAGE_KEYWORDS & set(words) else 0
    return overlap * 10 - extra + price_bonus


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


MAX_CONTAINER_CHARS = 600


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

    best: tuple[str, float, int] | None = None  # (sym, val, ctx_len)

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
                ctx_len = len(ctx)
                if ctx_len > MAX_CONTAINER_CHARS:
                    continue
                if container_matches(ctx):
                    if best is None or ctx_len < best[2]:
                        best = (sym, round(val, 2), ctx_len)
                    break
            cur = cur.parent

    return (best[0], best[1]) if best else None


def _fast_hit(html: str, tokens: list[str]) -> tuple[str, float] | None:
    if not any(c in html for c in "£€$"):
        return None
    low = html.lower()
    if tokens and not all(t in low for t in tokens):
        return None
    return _find_price_in_html(html, tokens)


def _html_to_text(html: str, max_chars: int = MAX_LLM_TEXT) -> str:
    """Strip noise tags and return plain text, truncated for LLM context."""
    soup = BeautifulSoup(html, "lxml")
    for t in soup(NOISE_TAGS):
        t.decompose()
    text = soup.get_text(" ", strip=True)
    return text[:max_chars]


def _token_overlap(html: str, tokens: list[str]) -> int:
    low = html.lower()
    return sum(1 for t in tokens if t in low)


def _scrape_sync(website: str, query: str) -> dict:
    """Synchronous multi-level crawl of a single website.

    Returns a dict with:
      hit:       price info dict if regex matched, else None
      html_text: cleaned text from the most relevant page (for LLM fallback)
      page_url:  URL that html_text came from
    """
    tokens = _tokenize_query(query)
    start = website.rstrip("/")
    host = urlparse(start).netloc

    best_html: str | None = None
    best_url: str | None = None
    best_overlap = -1

    def _track(url: str, raw_html: str):
        nonlocal best_html, best_url, best_overlap
        overlap = _token_overlap(raw_html, tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_html = raw_html
            best_url = url

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
                return {"hit": {"page_url": start, "symbol": hit[0], "price": hit[1]}}
            _track(start, home_html)

            lvl1 = _extract_links(start, home_html, host, tokens)[:TOP_LINKS]
            for u1 in lvl1:
                try:
                    html1 = c.get(u1).text
                except httpx.HTTPError:
                    continue
                hit = _fast_hit(html1, tokens)
                if hit:
                    return {"hit": {"page_url": u1, "symbol": hit[0], "price": hit[1]}}
                _track(u1, html1)

                lvl2 = _extract_links(u1, html1, host, tokens)[:TOP_SUBLINKS]
                for u2 in lvl2:
                    try:
                        html2 = c.get(u2).text
                    except httpx.HTTPError:
                        continue
                    hit = _fast_hit(html2, tokens)
                    if hit:
                        return {"hit": {"page_url": u2, "symbol": hit[0], "price": hit[1]}}
                    _track(u2, html2)
    except Exception:
        logger.debug("Scrape failed for %s", website, exc_info=True)

    fallback_text = _html_to_text(best_html) if best_html else None
    return {
        "hit": None,
        "html_text": fallback_text,
        "page_url": best_url,
        "best_overlap": best_overlap,
    }


async def _llm_extract_price(
    html_text: str,
    query: str,
    provider_name: str = "",
) -> tuple[str, float] | None:
    """Ask GPT to extract a price from scraped page text."""
    if not settings.openai_api_key:
        return None
    try:
        user_msg = f"Service: {query}\n"
        if provider_name:
            user_msg += (
                f"Provider: {provider_name}\n"
                f"Only extract a price that is specifically from {provider_name}. "
                f"Ignore prices from Apple, other providers, or general market references.\n"
            )
        user_msg += f"\nWebpage text:\n{html_text}"

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=100,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _PRICE_EXTRACT_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        content = resp.choices[0].message.content.strip()
        parsed = json.loads(content)
        price = parsed.get("price")
        symbol = parsed.get("currency_symbol", "£")
        if price is not None and isinstance(price, (int, float)) and price > 0:
            logger.info("LLM extracted price %s%.2f for %r", symbol, price, query)
            return symbol, round(float(price), 2)
    except Exception:
        logger.debug("LLM price extraction failed", exc_info=True)
    return None


def _domain_of(url: str) -> str:
    """Extract the registrable domain (e.g. 'kwik-fit.com') from a URL."""
    netloc = urlparse(url).netloc.lower().removeprefix("www.")
    return netloc


def _source_matches_provider(source_url: str, provider_website: str) -> bool:
    """Check if a Linkup source URL belongs to the provider's own domain."""
    if not source_url or not provider_website:
        return False
    return _domain_of(source_url) == _domain_of(provider_website)


_linkup_circuit_open_until: float = 0.0
_LINKUP_CIRCUIT_COOLDOWN = 120  # seconds to skip Linkup after a timeout
_LINKUP_TIMEOUT = 15  # seconds per search call
_linkup_sem = asyncio.Semaphore(1)


async def _linkup_search_price(
    query: str,
    provider_name: str,
    website: str,
) -> dict | None:
    """Use Linkup web search to find a specific service price.

    Scopes the search to the provider's website domain and validates
    that the returned source actually belongs to the provider.

    Calls are serialised via a semaphore so that a timeout on the first
    call trips the circuit breaker before subsequent calls are attempted.
    Fast errors (e.g. 504) do NOT trip the breaker because Linkup may
    succeed on the very next call.
    """
    global _linkup_circuit_open_until

    if LinkupClient is None or not settings.linkup_api_key:
        return None

    if time.monotonic() < _linkup_circuit_open_until:
        logger.debug("Linkup circuit open — skipping search for %s", provider_name)
        return None

    async with _linkup_sem:
        if time.monotonic() < _linkup_circuit_open_until:
            logger.debug("Linkup circuit open — skipping search for %s", provider_name)
            return None

        domain = _domain_of(website) if website else ""
        search_query = f"How much does {query} cost at {provider_name}?"
        logger.info("Linkup search query: %s", search_query)
        try:
            def _do_search():
                client = LinkupClient(api_key=settings.linkup_api_key)
                return client.search(
                    query=search_query,
                    depth="standard",
                    output_type="sourcedAnswer",
                )

            result = await asyncio.wait_for(
                asyncio.to_thread(_do_search),
                timeout=_LINKUP_TIMEOUT,
            )
            logger.info("Linkup search result for %s: %s", provider_name, result)
        except asyncio.TimeoutError:
            logger.warning(
                "Linkup search timed out after %ds for %s — opening circuit for %ds",
                _LINKUP_TIMEOUT, provider_name, _LINKUP_CIRCUIT_COOLDOWN,
            )
            _linkup_circuit_open_until = time.monotonic() + _LINKUP_CIRCUIT_COOLDOWN
            return None
        except Exception:
            logger.warning("Linkup search failed for %s", provider_name, exc_info=True)
            return None

        answer = getattr(result, "answer", "") or str(result)

        llm_hit = await _llm_extract_price(answer, query, provider_name=provider_name)
        if not llm_hit:
            return None

        sym, val = llm_hit

        source_url = website
        sources = getattr(result, "sources", [])
        has_provider_source = False
        for src in sources:
            src_url = getattr(src, "url", "") or ""
            if src_url and _source_matches_provider(src_url, website):
                source_url = src_url
                has_provider_source = True
                break

        if sources and not has_provider_source:
            logger.debug(
                "Linkup sources %s don't match provider domain %s — skipping",
                [getattr(s, "url", "") for s in sources[:3]], domain,
            )
            return None

        logger.info(
            "Linkup found price %s%.2f for %r at %s (source: %s)",
            sym, val, query, provider_name, source_url,
        )
        return {
            "page_url": source_url,
            "symbol": sym,
            "price": round(val, 2),
        }


async def scrape_provider_price(
    website: str,
    query: str,
    provider_name: str = "",
) -> dict | None:
    """Cascade: regex scraping → LLM extraction → Linkup web search.

    When settings.linkup_only is True, skips scraping/LLM and goes
    straight to Linkup.  Otherwise LLM and Linkup are only tried when
    the provider's website has at least MIN_OVERLAP_FOR_* query-token
    matches, preventing expensive API calls for clearly irrelevant
    businesses.
    """
    if settings.linkup_only:
        linkup_hit = await _linkup_search_price(query, provider_name, website)
        if linkup_hit:
            linkup_hit["source_type"] = "linkup"
            logger.info("[linkup] price for %s", provider_name)
            return linkup_hit
        return None

    result = await asyncio.to_thread(_scrape_sync, website, query)
    overlap = result.get("best_overlap", 0)

    if result.get("hit"):
        hit = result["hit"]
        hit["source_type"] = "scrape"
        logger.info("[regex] price on %s", hit["page_url"])
        return hit

    html_text = result.get("html_text")
    if html_text and overlap >= MIN_OVERLAP_FOR_LLM:
        llm_hit = await _llm_extract_price(html_text, query)
        if llm_hit:
            logger.info("[llm] price from %s", result.get("page_url"))
            return {
                "page_url": result.get("page_url") or website,
                "symbol": llm_hit[0],
                "price": llm_hit[1],
                "source_type": "llm_scrape",
            }
    elif overlap < MIN_OVERLAP_FOR_LLM:
        logger.debug(
            "Skipping LLM/Linkup for %s (overlap=%d < %d)",
            website, overlap, MIN_OVERLAP_FOR_LLM,
        )
        return None

    if overlap >= MIN_OVERLAP_FOR_LINKUP:
        linkup_hit = await _linkup_search_price(query, provider_name, website)
        if linkup_hit:
            linkup_hit["source_type"] = "linkup"
            logger.info("[linkup] price for %s", provider_name)
            return linkup_hit

    return None


async def scrape_and_store_prices(
    providers: list[dict],
    query: str,
    service_type_slug: str,
) -> dict[str, dict]:
    """Scrape prices for multiple providers concurrently and store as observations.

    Uses a three-tier extraction cascade per provider:
      1. Regex on scraped HTML
      2. LLM extraction on scraped page text
      3. Linkup web search

    Returns mapping of provider_id (str) -> observation dict.
    """
    scrapable = [p for p in providers if p.get("website")]
    if not scrapable:
        return {}

    logger.info(
        "Scraping prices for %d/%d providers (query=%r)",
        len(scrapable), len(providers), query,
    )

    tasks = [
        scrape_provider_price(p["website"], query, provider_name=p.get("name", ""))
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
        source_type = result.get("source_type", "scrape")
        now = datetime.now(timezone.utc)

        obs_doc = {
            "provider_id": pid,
            "service_type": service_type_slug,
            "category": service_type_slug,
            "price": result["price"],
            "currency": currency,
            "source_type": source_type,
            "source_url": result["page_url"],
            "location": provider["location"],
            "observed_at": now,
            "created_at": now,
        }
        try:
            await db.observations.insert_one(obs_doc)
            observations[str(pid)] = obs_doc
            logger.info(
                "[%s] Stored price %s%.2f for %s from %s",
                source_type, result["symbol"], result["price"],
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
