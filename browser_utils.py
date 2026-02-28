import random
import time

def create_stealth_page(playwright):
    """Launches Chromium and returns (browser, page) with stealth settings."""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080}
    )
    page = context.new_page()
    # Hide webdriver flag to evade basic detection
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return browser, page

def fetch_page(page, url, page_num):
    """Goto URL with retry on exception and random wait."""
    try:
        # Wait until dom is mostly loaded to ensure content is available
        response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Add a random wait to simulate human reading/loading time before fetching content
        page.wait_for_timeout(random.uniform(2000, 4000))
        return response, True
    except Exception as e:
        print(f"Error fetching page {page_num or url}: {e}. Retrying after 5 seconds...")
        time.sleep(5)
        return None, False

def wait_between_pages(page, min_s=2.5, max_s=10.0):
    """Wait for a random duration between page fetches."""
    sleep_duration = random.uniform(min_s, max_s)
    print(f"Waiting for {sleep_duration:.2f} seconds before the next page...")
    page.wait_for_timeout(sleep_duration * 1000)
