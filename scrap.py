import asyncio
import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# ── 1. Platform detector ──────────────────────────────────────
def detect_platform(url: str) -> str:
    if "amazon.in" in url:
        return "amazon"
    elif "flipkart.com" in url:
        return "flipkart"
    else:
        return "unsupported"

# ── 2. Price cleaner ──────────────────────────────────────────
# Turns "₹1,29,999" → 129999.0
def clean_price(raw: str) -> float | None:
    try:
        cleaned = raw.replace("₹", "").replace(",", "").strip()
        return float(cleaned)
    except:
        return None

# ── 3. Amazon scraper ─────────────────────────────────────────
async def scrape_amazon(page, url: str) -> dict:
    try:
        await page.goto(url, timeout=30000)

        # Wait for title to confirm page loaded
        await page.wait_for_selector("#productTitle", timeout=15000)

        # --- Title ---
        title_el = await page.query_selector("#productTitle")
        title = (await title_el.inner_text()).strip() if title_el else None

        # --- Price (.a-offscreen is the clean accessible price) ---
        price_el = await page.query_selector(".a-offscreen")
        raw_price = await price_el.inner_text() if price_el else None
        price = clean_price(raw_price) if raw_price else None

        # --- Stock status ---
        stock_el = await page.query_selector("#availability span")
        stock_text = (await stock_el.inner_text()).strip().lower() if stock_el else ""
        if "in stock" in stock_text:
            stock = "in_stock"
        elif "unavailable" in stock_text or "out of stock" in stock_text:
            stock = "out_of_stock"
        else:
            stock = "unknown"

        return {
            "url": url,
            "platform": "amazon",
            "product_title": title,
            "current_price": price,
            "stock_status": stock,
            "currency": "INR",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scrape_success": True,
            "error_message": None
        }

    except Exception as e:
        return {
            "url": url,
            "platform": "amazon",
            "product_title": None,
            "current_price": None,
            "stock_status": "unknown",
            "currency": "INR",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scrape_success": False,
            "error_message": str(e)
        }

# ── 4. Main runner ────────────────────────────────────────────
async def scrape(url: str) -> dict:
    platform = detect_platform(url)
    if platform == "unsupported":
        return {"error": "Unsupported platform"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # keep visible so Amazon doesn't block you
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        result = {"error": "Scraping failed"} # default error result in case something goes wrong before we can set it properly
        try:
            if platform == "amazon":
                result = await scrape_amazon(page, url)
        finally:
            await browser.close()  # ALWAYS runs, even if scrape fails

    return result

# ── 5. Entry point ────────────────────────────────────────────
if __name__ == "__main__":
    url = "https://www.amazon.in/HP-G10-Threads-Graphics-Windows/dp/B0G7YY5JV5/ref=sr_1_4?sr=8-4"
    result = asyncio.run(scrape(url))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    from database import save_scrape_result
    result = asyncio.run(scrape(url))
    save_scrape_result(result)
    print("Saved to database")