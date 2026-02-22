import json
import logging
import re

from openai import AsyncOpenAI

from app.config import settings
from app.db import get_db
from app.models.chat import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a concise assistant for a local services price comparison platform. \
Your job is to collect ALL required details before allowing a search.

## Available service categories
{service_types}

## Checklists — every item must be filled before status can be "ready"

DEVICE REPAIRS (phone, tablet, laptop, console, etc.)
  - service_type: what needs doing? (screen repair, battery replacement, charging port, camera…)
  - brand: iPhone / Samsung / Google / OnePlus / etc.
  - model: iPhone 15 Pro / Galaxy S24 / Pixel 8 / etc.

VEHICLE SERVICES (car, van, motorbike, etc.)
  - service_type: what needs doing? (tyre change, MOT, oil change, brake pads…)
  - make_model: Ford Focus / BMW 3 Series / etc. (optional for generic jobs like MOT or car wash)

TRADE / HOME SERVICES (electrician, plumber, cleaner, etc.)
  - specific_job: emergency call-out / boiler install / end-of-tenancy clean…

## Question order (when multiple items are missing)
Ask in this order, one question per turn:
  1. Service / repair type first
  2. Brand / make second
  3. Model / year third

## Rules
- Ask exactly ONE question per turn.
- Offer 3–4 concrete options in your question where helpful.
- Never ask for something the user already told you.
- No greetings, no filler.
- If the very first message already fills the entire checklist, mark ready immediately.

## search_query construction
Combine ALL collected info from the entire conversation into one clean phrase. \
NEVER use pronouns (it/this/that). NEVER use only the last message.

## Response format — raw JSON only, no markdown fences:
{{
  "collected": {{"service_type": "...", "brand": "...", "model": "..."}},
  "missing": ["brand", "model"],
  "status": "clarifying",
  "message": "your single question with options"
}}

When nothing is missing:
{{
  "collected": {{"service_type": "screen repair", "brand": "Apple", "model": "iPhone 15"}},
  "missing": [],
  "status": "ready",
  "message": "2–4 word confirmation",
  "search_query": "iPhone 15 screen repair"
}}

The "missing" array must list every checklist item not yet known. \
"status" MUST be "clarifying" whenever "missing" is non-empty.
"""


async def _get_service_types_summary() -> str:
    """Fetch service types from DB for the system prompt context."""
    db = get_db()
    categories: dict[str, list[str]] = {}
    async for doc in db.service_types.find({}, {"name": 1, "category": 1}).limit(100):
        cat = doc.get("category", "other")
        categories.setdefault(cat, []).append(doc["name"])

    if not categories:
        return "No service types defined yet — use your best judgement."

    lines = []
    for cat, names in categories.items():
        label = cat.replace("_", " ").title()
        lines.append(f"- {label}: {', '.join(names)}")
    return "\n".join(lines)


def _validate_response(parsed: dict) -> dict:
    """Override status to 'clarifying' if 'missing' is non-empty, regardless of what the LLM said."""
    missing = parsed.get("missing", [])
    if missing and parsed.get("status") == "ready":
        logger.info(
            "LLM said ready but missing=%s — overriding to clarifying", missing
        )
        first_missing = missing[0]
        parsed["status"] = "clarifying"
        parsed.pop("search_query", None)
        if first_missing in ("brand", "make_model"):
            parsed["message"] = "Which brand or make is it?"
        elif first_missing in ("model",):
            parsed["message"] = "Which model specifically?"
        elif first_missing in ("service_type", "specific_job"):
            parsed["message"] = "What service or repair do you need?"
    return parsed


async def chat(messages: list[ChatMessage]) -> ChatResponse:
    """Process a chat conversation and return either a clarifying question or a ready-to-search response."""
    if not settings.openai_api_key:
        last_msg = messages[-1].content if messages else ""
        return ChatResponse(
            status="ready",
            message="Searching now",
            search_query=last_msg,
        )

    service_summary = await _get_service_types_summary()
    system_prompt = _SYSTEM_PROMPT.format(service_types=service_summary)

    openai_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for m in messages:
        openai_messages.append({"role": m.role, "content": m.content})

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=300,
            response_format={"type": "json_object"},
            messages=openai_messages,
        )
        content = (resp.choices[0].message.content or "").strip()
        logger.debug("LLM raw content: %r", content)
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            raise ValueError(f"No JSON object found in LLM response: {content!r}")

        parsed = json.loads(json_match.group())
        logger.info("LLM raw response: %s", parsed)

        parsed = _validate_response(parsed)

        return ChatResponse(
            status=parsed["status"],
            message=parsed["message"],
            search_query=parsed.get("search_query"),
        )
    except Exception:
        logger.warning("Chat service failed, falling back to direct search", exc_info=True)
        last_msg = messages[-1].content if messages else ""
        return ChatResponse(
            status="ready",
            message="Searching now",
            search_query=last_msg,
        )
