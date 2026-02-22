import argparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import csv
import time
import random
import os

def crawl_pages(output_file="webpage_content.txt"):
    base_url = "https://alphastreet.com/india/category/transcripts/page/{}"
    page_num = 1
    
    print(f"Starting processing from page {page_num}...")
    
    # clear or create the raw content file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("")

    with sync_playwright() as p:
        # Launch browser in non-headless mode or headless, headless usually works if webdriver is hidden
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Hide webdriver flag to evade basic detection
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        while True:
            if page_num == 1:
                url = "https://alphastreet.com/india/category/transcripts/"
            else:
                url = base_url.format(page_num)
                
            print(f"Scraping {url}...")
            
            try:
                # Wait until dom is mostly loaded to ensure content is available
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Add a random wait to simulate human reading/loading time before fetching content
                page.wait_for_timeout(random.uniform(2000, 4000))
                
            except Exception as e:
                print(f"Error fetching page {page_num}: {e}. Retrying after 5 seconds...")
                time.sleep(5)
                continue
                
            if response is None or not response.ok:
                status = response.status if response else "Unknown"
                if status == 404:
                    print(f"Reached 404 on page {page_num}. No more pages to scrape.")
                else:
                    print(f"Failed to retrieve page {page_num} with status code {status}. Stopping.")
                break
                
            html_content = page.content()
            soup = BeautifulSoup(html_content, "html.parser")
            
            for a in soup.find_all('a', href=True):
                link_text = a.get_text(strip=True)
                if link_text:
                    a.string = f"{link_text} [{a['href']}]"

            text_content = soup.get_text(separator='\n', strip=True)
            
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- PAGE {page_num} ---\n")
                f.write(text_content)
                
            # Check if there's a 'Next' pagination link to be safe.
            has_next = any('Next' in str(a) for a in soup.find_all('a'))
            if not has_next:
                print(f"No 'Next' button found on page {page_num}. Stopping.")
                break

            page_num += 1
            sleep_duration = random.uniform(2.5, 10.0)
            print(f"Waiting for {sleep_duration:.2f} seconds before the next page...")
            page.wait_for_timeout(sleep_duration * 1000)

        browser.close()
    print("Crawling complete.")

def parse_and_generate_csv(input_file="webpage_content.txt", output_csv="transcripts.csv"):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist. Please run the crawler first.")
        return

    print(f"Reading {input_file} and generating {output_csv}...")
    
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    pages = re.split(r'\n--- PAGE (\d+) ---\n', content)
    
    all_data = []
    
    # pages list starts with an empty string or content before first page, followed by page number strings and page content
    for i in range(1, len(pages), 2):
        page_num = int(pages[i])
        page_content = pages[i+1]
        
        lines = page_content.split('\n')
        
        data_from_page = []
        for j, line in enumerate(lines):
            match = re.match(r'^(.*?)\s*\[(.*?)\]$', line)
            if match:
                text = match.group(1).strip()
                link = match.group(2).strip()
                
                if link.startswith('https://alphastreet.com/india/') and '/category/' not in link and len(link) > len('https://alphastreet.com/india/'):
                    date = ""
                    if j + 2 < len(lines) and lines[j+1].strip() == '●':
                        date = lines[j+2].strip()
                    
                    article_type = 'Transcript' if 'transcript' in text.lower() else 'Article'
                    data_from_page.append({'Page': page_num, 'Transcript': text, 'Date': date, 'Link': link, 'Type': article_type})
                    
        all_data.extend(data_from_page)
        if not data_from_page:
            print(f"Found 0 links on page {page_num}.")

    if all_data:
        with open(output_csv, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Page", "Transcript", "Date", "Link", "Type"])
            writer.writeheader()
            writer.writerows(all_data)
        print(f"\nAll pages processed. Total {len(all_data)} links saved to {output_csv}")
    else:
        print("\nNo links found in the file.")

def main():
    parser = argparse.ArgumentParser(description="AlphaStreet Transcripts Scraper")
    parser.add_argument("--crawl", action="store_true", help="Run the web crawler to generate webpage_content.txt")
    parser.add_argument("--csv", action="store_true", help="Parse webpage_content.txt to generate transcripts.csv")
    
    args = parser.parse_args()
    
    if not args.crawl and not args.csv:
        print("No action specified. Use --crawl, --csv, or both.")
        parser.print_help()
        return

    if args.crawl:
        crawl_pages()
        
    if args.csv:
        parse_and_generate_csv()

if __name__ == "__main__":
    main()
