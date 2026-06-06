"""Google Maps scraper using Playwright with anti-detection measures."""

import asyncio
import random
import re
from dataclasses import dataclass, field
from typing import Optional
from playwright.async_api import async_playwright, Page

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


@dataclass
class BusinessLead:
    name: str
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    reviews_count: int = 0
    rating: float = 0.0
    maps_url: str = ""
    has_website: bool = False
    # Filled by analyzer
    pagespeed_mobile: Optional[int] = None
    pagespeed_desktop: Optional[int] = None
    has_ssl: Optional[bool] = None
    is_mobile_friendly: Optional[bool] = None
    tech_stack: list = field(default_factory=list)
    web_looks_old: Optional[bool] = None
    # Filled by scorer
    urgency_score: Optional[int] = None
    problem_summary: str = ""
    whatsapp_message: str = ""


async def human_delay(min_s: float = 2.0, max_s: float = 5.0):
    await asyncio.sleep(random.uniform(min_s, max_s))


async def setup_context(playwright):
    browser = await playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
    )
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1440, "height": 900},
        locale="es-ES",
        timezone_id="Europe/Madrid",
    )
    await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    return browser, context


async def scroll_feed(page: Page, target: int, min_s: float, max_s: float):
    for _ in range(25):
        links = await page.query_selector_all('a[href*="/maps/place/"]')
        if len(links) >= target:
            break
        await page.evaluate("""
            const feed = document.querySelector('div[role="feed"]');
            if (feed) feed.scrollBy(0, 1000);
        """)
        await human_delay(min_s, max_s)


async def extract_detail(page: Page) -> dict:
    """Extract all fields from a detail page already loaded in `page`."""
    data = {"address": "", "phone": "", "website": "", "reviews_count": 0, "rating": 0.0}

    # Wait explicitly for the info rows — more reliable than networkidle alone
    try:
        await page.wait_for_selector('[data-item-id]', timeout=8000)
    except Exception:
        await asyncio.sleep(3)

    # Rating: span[aria-hidden="true"] inside .F7nice
    try:
        rating_el = await page.query_selector('.F7nice span[aria-hidden="true"]')
        if rating_el:
            txt = (await rating_el.inner_text()).strip()
            data["rating"] = float(txt.replace(",", "."))
    except Exception:
        pass

    # Reviews: span[role="img"] with aria-label like "68 reseñas"
    try:
        rev_el = await page.query_selector(
            'span[role="img"][aria-label*="reseña"], span[role="img"][aria-label*="review"]'
        )
        if rev_el:
            label = (await rev_el.get_attribute("aria-label")) or ""
            nums = re.findall(r"\d+", label.replace(".", "").replace(",", ""))
            if nums:
                data["reviews_count"] = int(nums[0])
    except Exception:
        pass

    # Address / phone / website via data-item-id
    # Wait a bit extra for 'authority' (website) which loads last
    await asyncio.sleep(1)
    try:
        rows = await page.query_selector_all('[data-item-id]')
        for row in rows:
            item_id = (await row.get_attribute("data-item-id")) or ""

            if item_id == "address" and not data["address"]:
                txt = (await row.inner_text()).strip()
                data["address"] = txt.split("\n")[0].strip()

            elif "phone:tel" in item_id and not data["phone"]:
                phone = item_id.replace("phone:tel:", "").strip()
                if not phone:
                    phone = (await row.inner_text()).strip().split("\n")[0].strip()
                data["phone"] = phone

            elif item_id == "authority" and not data["website"]:
                # Google Maps renders the domain as plain text (no <a> tag).
                # inner_text() = '\noscarpaloshairsalon.com'
                # First line is a Material icon char, domain is on a subsequent line.
                raw = (await row.inner_text()).strip()
                for line in raw.split("\n"):
                    line = line.strip()
                    # A valid domain: has a dot, no spaces, only ASCII printable chars
                    if line and "." in line and " " not in line and line.isascii():
                        data["website"] = ("https://" if not line.startswith("http") else "") + line
                        break
    except Exception:
        pass

    return data


async def scrape_google_maps(query: str, max_results: int, min_delay: float, max_delay: float) -> list[BusinessLead]:
    leads: list[BusinessLead] = []

    async with async_playwright() as pw:
        browser, context = await setup_context(pw)
        # Use a SINGLE page — navigate from search to detail and back
        # This is key: data-item-id elements only render when navigated from Maps search context
        page = await context.new_page()

        try:
            url = "https://www.google.com/maps/search/" + query.replace(" ", "+")
            print(f"[scraper] {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await human_delay(min_delay, max_delay)

            # Accept cookies
            for selector in ['button[aria-label*="Aceptar"]', 'button[aria-label*="Accept all"]']:
                try:
                    btn = await page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        await btn.click()
                        await human_delay(1, 2)
                        break
                except Exception:
                    continue

            await page.wait_for_selector('div[role="feed"]', timeout=15000)
            await human_delay(1, 2)

            print(f"[scraper] Scrolling for {max_results} results...")
            await scroll_feed(page, max_results, min_delay, max_delay)

            # Collect unique place hrefs + names BEFORE navigating away
            links = await page.query_selector_all('a[href*="/maps/place/"]')
            seen = set()
            places = []  # list of (name, href)
            for lnk in links:
                name = (await lnk.get_attribute("aria-label") or "").strip()
                href = (await lnk.get_attribute("href") or "").strip()
                key = href.split("/data=")[0]
                if key and key not in seen and name:
                    seen.add(key)
                    places.append((name, href))

            places = places[:max_results]
            print(f"[scraper] {len(places)} unique places — extracting details...")

            for i, (name, href) in enumerate(places):
                try:
                    print(f"[scraper] ({i+1}/{len(places)}) {name}")
                    # Navigate in same page — this preserves Maps session context
                    await page.goto(href, wait_until="networkidle", timeout=30000)
                    detail = await extract_detail(page)

                    leads.append(BusinessLead(
                        name=name,
                        address=detail["address"],
                        phone=detail["phone"],
                        website=detail["website"],
                        reviews_count=detail["reviews_count"],
                        rating=detail["rating"],
                        maps_url=href,
                        has_website=bool(detail["website"]),
                    ))
                    print(f"    tel={detail['phone'] or '—'}  web={detail['website'] or '—'}")
                    await human_delay(min_delay, max_delay)

                except Exception as e:
                    print(f"    [warn] Skipping {i+1}: {e}")
                    continue

        finally:
            await browser.close()

    return leads
