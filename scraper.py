import csv
import json
import os
import random
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

PROGRESS_FILE = "progress.json"
DATA_DIR = "transcripts_data"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=4)

def sanitize_filename(url):
    """Extracts a sensible filename from the URL."""
    path = urlparse(url).path
    filename = path.strip('/').split('/')[-1]
    if not filename:
        filename = "index"
    return f"{filename}.txt"

def fetch_transcripts(csv_file="transcripts.csv"):
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    progress = load_progress()

    urls_to_scrape = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = row.get("Link")
            if link and link not in progress:
                urls_to_scrape.append(link)

    if not urls_to_scrape:
        print("All URLs have already been scraped or attempted.")
        return

    import browser_utils

    print(f"Found {len(urls_to_scrape)} new URLs to scrape.")

    with sync_playwright() as p:
        browser, page = browser_utils.create_stealth_page(p)

        for i, url in enumerate(urls_to_scrape):
            print(f"[{i+1}/{len(urls_to_scrape)}] Scraping {url}...")
            
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Simulate human reading time + avoid rapid requests triggering rate limits
                read_time = random.uniform(3000, 8000)
                page.wait_for_timeout(read_time)
                
                if response and response.ok:
                    # Extract all text from the page
                    text_content = page.locator("body").inner_text()
                    
                    filename = sanitize_filename(url)
                    filepath = os.path.join(DATA_DIR, filename)
                    
                    with open(filepath, "w", encoding="utf-8") as out_f:
                        out_f.write(f"URL: {url}\n\n")
                        out_f.write(text_content)
                    
                    progress[url] = {"status": "success", "file": filepath}
                    print(f"  -> Saved successfully to {filepath}")
                else:
                    status_code = response.status if response else "Unknown"
                    print(f"  -> Failed with status {status_code}")
                    progress[url] = {"status": "failed", "error": f"HTTP {status_code}"}
                    
            except Exception as e:
                print(f"  -> Exception occurred: {e}")
                progress[url] = {"status": "failed", "error": str(e)}
            
            finally:
                page.close()
                save_progress(progress)

            # Wait between requests to be gentle to the server
            sleep_duration = random.uniform(4.0, 10.0)
            print(f"  -> Waiting {sleep_duration:.2f}s before next request...\n")
            time.sleep(sleep_duration)

        browser.close()
        print("Finished scraping pending URLs.")

if __name__ == "__main__":
    fetch_transcripts()
