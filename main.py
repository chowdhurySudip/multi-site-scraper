import argparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import os

from scraper import fetch_transcripts
import browser_utils
import page_parser

def _iter_pages(page):
    """
    Private generator that handles pagination logic.
    Yields (page_num, soup, lines) for each page.
    """
    page_num = 1
    while True:
        url = page_parser.build_page_url(page_num)
        print(f"Scraping {url}...")
        
        response, ok = browser_utils.fetch_page(page, url, page_num)
        if not ok:
            # fetch_page already handles retry/wait; if it returns False, it's a stop condition (like 404)
            if response and response.status == 404:
                print(f"Reached 404 on page {page_num}. No more pages.")
            else:
                status = response.status if response else "Unknown"
                print(f"Stopped at page {page_num} with status {status}.")
            break

        html_content = page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Annotate links so they are preserved in text dumps
        page_parser.annotate_links(soup)
        
        text_content = soup.get_text(separator='\n', strip=True)
        lines = text_content.split('\n')
        
        yield page_num, soup, lines

        if not page_parser.has_next_page(soup):
            print(f"No 'Next' button found on page {page_num}. Stopping.")
            break

        page_num += 1
        browser_utils.wait_between_pages(page)

def crawl_to_file(output_file="webpage_content.txt"):
    """Runs a full crawl and saves raw text content to a file."""
    print("Starting full crawl to file...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("")

    with sync_playwright() as p:
        browser, page = browser_utils.create_stealth_page(p)
        
        for page_num, soup, lines in _iter_pages(page):
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- PAGE {page_num} ---\n")
                f.write('\n'.join(lines))
        
        browser.close()
    print("Crawling to file complete.")

def parse_to_csv(input_file="webpage_content.txt", output_csv="transcripts.csv"):
    """Parses raw text content file and generates a structured CSV."""
    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist. Please run the crawler first.")
        return

    print(f"Reading {input_file} and generating {output_csv}...")
    
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    pages = re.split(r'\n--- PAGE (\d+) ---\n', content)
    all_entries = []
    
    # pages list starts with potential junk, then pairs of (page_num_str, content)
    for i in range(1, len(pages), 2):
        page_num = int(pages[i])
        page_content = pages[i+1]
        lines = page_content.split('\n')
        
        page_entries = []
        for j in range(len(lines)):
            entry = page_parser.parse_entry(lines, j)
            if entry:
                entry['Page'] = page_num
                page_entries.append(entry)
                    
        all_entries.extend(page_entries)
        if not page_entries:
            print(f"Found 0 links on page {page_num}.")

    if all_entries:
        with open(output_csv, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Page", "Transcript", "Date", "Link", "Type"])
            writer.writeheader()
            writer.writerows(all_entries)
        print(f"\nAggregation complete. Total {len(all_entries)} links saved to {output_csv}")
    else:
        print("\nNo links found in the source file.")

def update_transcripts_csv(output_csv="transcripts.csv"):
    """
    Incremental update: paginates until a known URL is found.
    Prepends new entries to the top of the existing CSV.
    """
    existing_urls = set()
    if os.path.exists(output_csv):
        with open(output_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_urls.add(row["Link"].strip())
        print(f"Loaded {len(existing_urls)} existing URLs from {output_csv}")
    else:
        print(f"{output_csv} not found - creating fresh file.")

    new_entries = []
    stop_pagination = False

    with sync_playwright() as p:
        browser, page = browser_utils.create_stealth_page(p)

        for page_num, soup, lines in _iter_pages(page):
            page_new_entries = []
            for j in range(len(lines)):
                entry = page_parser.parse_entry(lines, j)
                if not entry:
                    continue
                
                if entry['Link'] in existing_urls:
                    print(f"Found existing URL on page {page_num}: {entry['Link']}")
                    stop_pagination = True
                    break
                
                entry['Page'] = page_num
                page_new_entries.append(entry)

            print(f"  Found {len(page_new_entries)} new entries on page {page_num}.")
            new_entries.extend(page_new_entries)
            
            if stop_pagination:
                print("Stopping pagination - newer entries collected.")
                break

        browser.close()

    if not new_entries:
        print("No new transcript links found.")
        return

    # Prepends new entries
    existing_rows = []
    if os.path.exists(output_csv):
        with open(output_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)

    all_rows = new_entries + existing_rows
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Page", "Transcript", "Date", "Link", "Type"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Updated {output_csv}: {len(new_entries)} new, {len(all_rows)} total.")

def main():
    parser = argparse.ArgumentParser(description="AlphaStreet Transcripts Scraper")
    parser.add_argument("--crawl", action="store_true", help="Full crawl to webpage_content.txt")
    parser.add_argument("--csv", action="store_true", help="Parse webpage_content.txt to transcripts.csv")
    parser.add_argument("--fetch-transcripts", action="store_true", help="Fetch individual transcripts based on CSV")
    parser.add_argument("--crawl-new", action="store_true", help="Incremental update of transcripts.csv")

    args = parser.parse_args()

    if not any([args.crawl, args.csv, args.fetch_transcripts, args.crawl_new]):
        parser.print_help()
        return

    if args.crawl:
        crawl_to_file()
    if args.csv:
        parse_to_csv()
    if args.fetch_transcripts:
        fetch_transcripts("transcripts.csv")
    if args.crawl_new:
        update_transcripts_csv()

if __name__ == "__main__":
    main()
