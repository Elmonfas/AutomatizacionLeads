"""Web presence analyzer using PageSpeed Insights (no API key) + HTML inspection."""

import asyncio
import re
from typing import Optional
import httpx

from scraper import BusinessLead

PAGESPEED_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

OLD_TECH_SIGNALS = [
    "jquery/1.", "jquery/2.",
    "bootstrap/3.", "bootstrap/2.",
    "font-awesome/4.",
    "table width=", "bgcolor=",
    "<!doctype html public",
    "frameset", "<frame ",
]

OLD_CMS_PATTERNS = [
    r"wordpress [3-4]\.",
    r"joomla [1-2]\.",
    r"drupal [6-7]\.",
]


async def fetch_pagespeed(url: str, strategy: str) -> dict:
    """Call PageSpeed without API key — free tier, ~1 req/s."""
    params = {"url": url, "strategy": strategy}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(PAGESPEED_ENDPOINT, params=params)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {}


def extract_score(psi_data: dict) -> Optional[int]:
    try:
        score = psi_data["lighthouseResult"]["categories"]["performance"]["score"]
        return int(score * 100)
    except (KeyError, TypeError):
        return None


async def fetch_html(url: str) -> Optional[str]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WebAnalyzer/1.0)"}
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.text
    except Exception:
        pass
    return None


EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
# Domains to ignore when extracting emails
EMAIL_BLACKLIST = {
    "example.com", "sentry.io", "wixpress.com", "squarespace.com",
    "wordpress.com", "shopify.com", "googletagmanager.com",
    "schema.org", "w3.org", "yoursite.com", "domain.com",
}


def extract_email(html: str) -> str:
    """Return the best contact email found in the HTML, or empty string."""
    # Prefer mailto: links
    mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html)
    candidates = mailto + EMAIL_RE.findall(html)
    seen = set()
    for email in candidates:
        email = email.lower().strip(".,;\"'")
        domain = email.split("@")[-1]
        if domain in EMAIL_BLACKLIST:
            continue
        # Skip image/asset file extensions accidentally matched
        if re.search(r'\.(png|jpg|gif|svg|js|css|woff)$', domain):
            continue
        if email not in seen:
            seen.add(email)
            return email
    return ""


def detect_old_tech(html: str) -> tuple[list[str], bool]:
    html_lower = html.lower()
    detected = [s for s in OLD_TECH_SIGNALS if s in html_lower]
    for pattern in OLD_CMS_PATTERNS:
        if re.search(pattern, html_lower):
            detected.append("old-cms-detected")
            break
    return detected, len(detected) > 0


async def analyze_business(lead: BusinessLead) -> BusinessLead:
    if not lead.has_website:
        print(f"  [analyzer] {lead.name}: sin web")
        return lead

    url = lead.website
    print(f"  [analyzer] {lead.name}: {url}")

    lead.has_ssl = url.lower().startswith("https://")

    # PageSpeed (no key needed)
    psi_mobile = await fetch_pagespeed(url, "mobile")
    lead.pagespeed_mobile = extract_score(psi_mobile)

    psi_desktop = await fetch_pagespeed(url, "desktop")
    lead.pagespeed_desktop = extract_score(psi_desktop)

    if lead.pagespeed_mobile is not None:
        lead.is_mobile_friendly = lead.pagespeed_mobile >= 50

    # HTML tech detection + email extraction
    html = await fetch_html(url)
    if html:
        signals, old = detect_old_tech(html)
        lead.tech_stack = signals
        lead.web_looks_old = old
        if not lead.email:
            lead.email = extract_email(html)

    print(
        f"    → mobile={lead.pagespeed_mobile} desktop={lead.pagespeed_desktop} "
        f"ssl={lead.has_ssl} email={lead.email or '—'}"
    )
    await asyncio.sleep(1.2)
    return lead


async def analyze_all(leads: list[BusinessLead]) -> list[BusinessLead]:
    results = []
    for lead in leads:
        results.append(await analyze_business(lead))
    return results
