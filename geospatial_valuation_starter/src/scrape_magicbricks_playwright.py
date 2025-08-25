"""
Scrape real estate listings with Playwright (JS-friendly).

USAGE:
  python src/scrape_magicbricks_playwright.py --url "https://www.magicbricks.com/property-for-sale/residential-real-estate?City=bangalore" --pages 2 --delay 2 --out_csv data/raw/listings_raw.csv

NOTE: You MUST inspect the website in DevTools and update CSS/XPath SELECTORS below.
"""

import time, csv, argparse, random
from pathlib import Path
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

DEFAULT_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def parse_cards(html: str) -> List[Dict]:
    """
    Parse listing cards from HTML using BeautifulSoup.
    >>> IMPORTANT: Update the selectors carefully after inspecting the site!
    """
    soup = BeautifulSoup(html, "lxml")
    results = []
    # --- TODO: Update card selector
    cards = soup.select("div.mb-srp__card") or soup.select("article") or []
    for c in cards:
        # Title / heading
        title = (c.select_one("h2") or c.select_one("h3") or c.select_one("[data-testid='card-title']"))
        title = title.get_text(strip=True) if title else None

        # Price
        price = (c.select_one(".mb-srp__card__price--amount") or c.select_one("[data-testid='price']"))
        price = price.get_text(strip=True) if price else None

        # Locality
        locality = (c.select_one(".mb-srp__card__location") or c.select_one("[data-testid='locality']"))
        locality = locality.get_text(strip=True) if locality else None

        # Beds/BHK
        bhk = None
        bhk_el = c.find(lambda tag: tag.name in ["span","div","li"] and "BHK" in tag.get_text())
        if bhk_el:
            bhk = bhk_el.get_text(strip=True)

        # Area
        area = None
        area_el = c.find(lambda tag: tag.name in ["span","div","li"] and ("sqft" in tag.get_text().lower() or "sq. ft" in tag.get_text().lower()))
        if area_el:
            area = area_el.get_text(strip=True)

        # URL
        link = None
        a = c.select_one("a[href]")
        if a:
            href = a.get("href", "")
            if href and not href.startswith("#"):
                link = href

        results.append({
            "title": title,
            "price_text": price,
            "bhk_text": bhk,
            "area_text": area,
            "locality": locality,
            "url": link,
        })
    return results

def scroll_lazy(page, times=8, pause=1.5):
    for _ in range(times):
        page.mouse.wheel(0, 4000)
        time.sleep(pause)

def run(url: str, pages: int, delay: float, out_csv: str):
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)

    ua = random.choice(DEFAULT_UAS)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=ua)
        page = ctx.new_page()
        all_rows: List[Dict] = []

        for i in range(1, pages+1):
            page_url = url if i == 1 else f"{url}&page={i}"
            print(f"[page {i}] Navigating: {page_url}")
            page.goto(page_url, wait_until="domcontentloaded", timeout=120000)
            time.sleep(delay)
            scroll_lazy(page, times=10, pause=1.0)
            html = page.content()
            rows = parse_cards(html)
            print(f"  parsed {len(rows)} rows")
            all_rows.extend(rows)
            time.sleep(delay)

        browser.close()

    # Write CSV
    keys = ["title","price_text","bhk_text","area_text","locality","url"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in all_rows:
            writer.writerow(r)
    print(f"Saved {len(all_rows)} rows -> {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Search URL for your city/filters")
    ap.add_argument("--pages", type=int, default=2, help="How many pages to paginate")
    ap.add_argument("--delay", type=float, default=2.0, help="Seconds to sleep between actions")
    ap.add_argument("--out_csv", default="data/raw/listings_raw.csv")
    args = ap.parse_args()
    run(args.url, args.pages, args.delay, args.out_csv)
