import asyncio
import email as email_lib
import imaplib
import json
import logging
import random
import re
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid
from typing import Optional
from urllib.parse import urlparse

import httpx
from bson import ObjectId
from openai import AsyncOpenAI

from app.config import settings
from app.db import get_db

logger = logging.getLogger(__name__)

_HTTPX_TIMEOUT = httpx.Timeout(connect=4, read=8, write=4, pool=4)


def is_email_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.from_email)


def _extract_domain(website: str) -> Optional[str]:
    if not website:
        return None
    if not website.startswith(("http://", "https://")):
        website = "https://" + website
    parsed = urlparse(website)
    domain = parsed.hostname
    if domain and domain.startswith("www."):
        domain = domain[4:]
    return domain


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_IGNORE_DOMAINS = {
    "sentry.io", "wixpress.com", "googleapis.com", "google.com",
    "facebook.com", "twitter.com", "instagram.com", "schema.org",
    "w3.org", "example.com", "cloudflare.com",
}


async def _scrape_email_from_website(website: str) -> Optional[str]:
    """Try to find a contact email on the provider's website."""
    if not website:
        return None
    if not website.startswith(("http://", "https://")):
        website = "https://" + website

    provider_domain = _extract_domain(website)

    try:
        async with httpx.AsyncClient(
            timeout=_HTTPX_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PriceBot/1.0)"},
        ) as client:
            pages_to_check = [website]
            resp = await client.get(website)
            text = resp.text.lower()
            for suffix in ["/contact", "/kontakt", "/about", "/impressum"]:
                if suffix in text:
                    pages_to_check.append(website.rstrip("/") + suffix)

            for page_url in pages_to_check[:3]:
                try:
                    r = await client.get(page_url)
                    found = _EMAIL_RE.findall(r.text)
                    for addr in found:
                        addr_domain = addr.split("@")[1].lower()
                        if addr_domain in _IGNORE_DOMAINS:
                            continue
                        if provider_domain and addr_domain == provider_domain:
                            return addr
                        return addr
                except Exception:
                    continue
    except Exception:
        logger.debug("Failed to scrape email from %s", website, exc_info=True)

    return None


OVERRIDE_RECIPIENT = "janoscsampai@live.de"


async def find_provider_email(provider: dict) -> Optional[str]:
    """Always sends to the override recipient for now."""
    return OVERRIDE_RECIPIENT


_FIRST_NAMES = [
    "James", "Emma", "Oliver", "Sophie", "Lucas", "Mia", "Ethan", "Chloe",
    "Noah", "Lily", "Leo", "Anna", "Max", "Clara", "Tom", "Alice",
    "Ben", "Sarah", "Daniel", "Laura", "Henry", "Emily", "Jack", "Hannah",
]

_DRAFT_PROMPT = (
    "You are writing a brief, professional email on behalf of a potential customer "
    "to a local service provider. The email should:\n"
    "1. Be polite and concise (3-5 sentences)\n"
    "2. Mention the specific service the customer needs\n"
    "3. Ask for their pricing / a quote\n"
    "4. Ask them to reply to this email with their rates\n"
    "5. Sign off with ONLY the first name provided — no last name, no phone number, "
    "no address, no contact information whatsoever\n\n"
    "Do NOT include a subject line — just the email body.\n"
    "Do NOT use placeholder brackets like [Name] or [Your Contact Information].\n"
    "Do NOT add any contact details after the name in the sign-off."
)


def _random_name() -> str:
    return random.choice(_FIRST_NAMES)


async def draft_inquiry_email(
    provider_name: str,
    service_name: str,
    provider_description: Optional[str] = None,
) -> tuple[str, str]:
    """Draft a personalized inquiry email. Returns (subject, body)."""
    sender_name = _random_name()

    context = f"Provider: {provider_name}"
    if provider_description:
        context += f"\nProvider description: {provider_description}"
    context += f"\nService needed: {service_name}"
    context += f"\nCustomer first name: {sender_name}"

    subject = f"Price inquiry: {service_name}"

    if not settings.openai_api_key:
        body = (
            f"Dear {provider_name},\n\n"
            f"I am looking for {service_name} and came across your business. "
            f"Could you please let me know your pricing for this service?\n\n"
            f"I would appreciate it if you could reply to this email with your rates.\n\n"
            f"Thank you for your time.\n\n"
            f"Best regards,\n{sender_name}"
        )
        return subject, body

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=300,
            messages=[
                {"role": "system", "content": _DRAFT_PROMPT},
                {"role": "user", "content": context},
            ],
        )
        body = resp.choices[0].message.content.strip()
        return subject, body
    except Exception:
        logger.warning("LLM email drafting failed, using template", exc_info=True)
        body = (
            f"Dear {provider_name},\n\n"
            f"I am looking for {service_name} and came across your business. "
            f"Could you please let me know your pricing for this service?\n\n"
            f"I would appreciate it if you could reply to this email with your rates.\n\n"
            f"Thank you for your time.\n\n"
            f"Best regards,\n{sender_name}"
        )
        return subject, body


def _send_email(to_addr: str, subject: str, body: str, message_id: str) -> None:
    """Send an email via SMTP (blocking — run in a thread)."""
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = formataddr(("Plumline", settings.from_email))
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg["Reply-To"] = settings.from_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.from_email, [to_addr], msg.as_string())


async def send_inquiry(provider_id: str, service_type_slug: str) -> dict:
    """Find provider email, draft & send an inquiry, store in DB."""
    db = get_db()

    provider = await db.providers.find_one({"_id": ObjectId(provider_id)})
    if not provider:
        raise ValueError(f"Provider {provider_id} not found")

    existing = await db.inquiries.find_one({
        "provider_id": ObjectId(provider_id),
        "service_type": service_type_slug,
        "status": {"$in": ["sent", "replied"]},
    })
    if existing:
        existing["_id"] = str(existing["_id"])
        existing["provider_id"] = str(existing["provider_id"])
        return existing

    email_to = await find_provider_email(provider)
    if not email_to:
        raise ValueError(f"No email found for provider {provider['name']}")

    stype_doc = await db.service_types.find_one({"slug": service_type_slug})
    service_name = stype_doc["name"] if stype_doc else service_type_slug.replace("_", " ").title()

    subject, body = await draft_inquiry_email(
        provider_name=provider["name"],
        service_name=service_name,
        provider_description=provider.get("description"),
    )

    message_id = make_msgid(domain=settings.from_email.split("@")[-1] if "@" in settings.from_email else "plumline.local")

    await asyncio.to_thread(_send_email, email_to, subject, body, message_id)

    doc = {
        "provider_id": ObjectId(provider_id),
        "provider_name": provider["name"],
        "service_type": service_type_slug,
        "email_to": email_to,
        "subject": subject,
        "body": body,
        "message_id": message_id,
        "status": "sent",
        "reply_body": None,
        "extracted_price": None,
        "extracted_currency": None,
        "sent_at": datetime.now(timezone.utc),
        "replied_at": None,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.inquiries.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["provider_id"] = provider_id
    return doc


_PRICE_EXTRACT_PROMPT = (
    "You are extracting pricing information from an email reply. "
    "The email is a response to a price inquiry about a specific service.\n\n"
    "Extract the price and currency if mentioned. If multiple prices are given, "
    "use the lowest/base price.\n\n"
    'Reply with ONLY a JSON object: {"price": <number or null>, "currency": "<3-letter code or null>"}\n'
    "If no price is found, return null for both fields."
)


async def _extract_price_from_reply(reply_body: str, service_name: str) -> tuple[Optional[float], Optional[str]]:
    """Use LLM to extract a price from an email reply."""
    if not settings.openai_api_key:
        return None, None

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=100,
            messages=[
                {"role": "system", "content": _PRICE_EXTRACT_PROMPT},
                {"role": "user", "content": f"Service: {service_name}\n\nEmail reply:\n{reply_body}"},
            ],
        )
        parsed = json.loads(resp.choices[0].message.content.strip())
        price = parsed.get("price")
        currency = parsed.get("currency", "EUR")
        if price and isinstance(price, (int, float)) and price > 0:
            return float(price), currency
        return None, None
    except Exception:
        logger.warning("Failed to extract price from reply", exc_info=True)
        return None, None


def _check_imap_replies(known_message_ids: set[str]) -> list[dict]:
    """Check IMAP inbox for replies to our inquiries (blocking — run in a thread).

    Only fetches full bodies for messages whose In-Reply-To/References match
    a known inquiry Message-ID, keeping things fast.
    """
    if not settings.imap_host or not settings.smtp_user or not known_message_ids:
        return []

    replies = []
    try:
        conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        conn.socket().settimeout(10)
        conn.login(settings.smtp_user, settings.smtp_password)
        conn.select("INBOX")

        _, msg_nums = conn.search(None, "UNSEEN")
        if not msg_nums[0]:
            conn.logout()
            return []

        nums = msg_nums[0].split()

        # Batch-fetch just headers to quickly identify relevant replies
        num_range = b",".join(nums)
        _, header_data = conn.fetch(num_range, "(BODY.PEEK[HEADER.FIELDS (In-Reply-To References From Subject)])")

        relevant_nums = []
        for i in range(0, len(header_data), 2):
            item = header_data[i]
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            seq_str = item[0].split()[0]
            hdr = email_lib.message_from_bytes(item[1])
            in_reply_to = (hdr.get("In-Reply-To") or "").strip()
            references = (hdr.get("References") or "").strip()

            matched = False
            for mid in known_message_ids:
                if mid in in_reply_to or mid in references:
                    matched = True
                    break
            if matched:
                relevant_nums.append((seq_str, in_reply_to, references, hdr.get("From", ""), hdr.get("Subject", "")))

        for seq, in_reply_to, references, from_addr, subject in relevant_nums:
            _, body_data = conn.fetch(seq, "(RFC822)")
            raw = body_data[0][1]
            msg = email_lib.message_from_bytes(raw)

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode("utf-8", errors="replace")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="replace")

            # Mark as seen
            conn.store(seq, "+FLAGS", "\\Seen")

            replies.append({
                "in_reply_to": in_reply_to,
                "references": references,
                "from_addr": from_addr,
                "subject": subject,
                "body": body,
            })

        conn.logout()
    except Exception:
        logger.warning("IMAP reply check failed", exc_info=True)

    return replies


async def check_for_replies() -> int:
    """Check for email replies and process them into observations.

    Returns the number of new replies processed.
    """
    if not is_email_configured() or not settings.imap_host:
        return 0

    db = get_db()

    pending_inquiries = []
    async for inq in db.inquiries.find({"status": "sent"}):
        pending_inquiries.append(inq)

    if not pending_inquiries:
        return 0

    msg_id_map = {inq["message_id"]: inq for inq in pending_inquiries}

    replies = await asyncio.to_thread(_check_imap_replies, set(msg_id_map.keys()))
    if not replies:
        return 0

    processed = 0
    for reply in replies:
        inquiry = None
        for ref in [reply["in_reply_to"], reply.get("references", "")]:
            if ref in msg_id_map:
                inquiry = msg_id_map[ref]
                break
            for mid, inq in msg_id_map.items():
                if mid in ref:
                    inquiry = inq
                    break
            if inquiry:
                break

        if not inquiry:
            continue

        stype_doc = await db.service_types.find_one({"slug": inquiry["service_type"]})
        service_name = stype_doc["name"] if stype_doc else inquiry["service_type"]

        price, currency = await _extract_price_from_reply(reply["body"], service_name)

        now = datetime.now(timezone.utc)
        update: dict = {
            "status": "replied",
            "reply_body": reply["body"][:5000],
            "replied_at": now,
        }
        if price:
            update["extracted_price"] = price
            update["extracted_currency"] = currency

        await db.inquiries.update_one(
            {"_id": inquiry["_id"]},
            {"$set": update},
        )

        provider = await db.providers.find_one({"_id": inquiry["provider_id"]})
        source_url = f"mailto:{inquiry['email_to']}"

        observation_doc = {
            "provider_id": inquiry["provider_id"],
            "service_type": inquiry["service_type"],
            "category": stype_doc["category"] if stype_doc else inquiry["service_type"],
            "price": price if price else 0,
            "currency": currency if currency else "EUR",
            "source_type": "quote",
            "source_url": source_url,
            "location": provider["location"] if provider else {"type": "Point", "coordinates": [0, 0]},
            "observed_at": now,
            "created_at": now,
            "inquiry_reply": reply["body"][:2000],
        }

        if price and price > 0:
            await db.observations.insert_one(observation_doc)
            logger.info(
                "Created observation from email reply: provider=%s, price=%.2f %s",
                inquiry["provider_name"], price, currency,
            )
        else:
            observation_doc["price"] = 0
            observation_doc["source_type"] = "quote"
            await db.observations.insert_one(observation_doc)
            logger.info(
                "Stored email reply as observation (no price extracted): provider=%s",
                inquiry["provider_name"],
            )

        processed += 1

    logger.info("Processed %d email replies", processed)
    return processed
