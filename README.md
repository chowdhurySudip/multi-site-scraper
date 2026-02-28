# Multi-Site Scraper

A modular, stealthy web scraping engine designed for extracting financial transcripts and articles from various websites.

## Current Support
- **AlphaStreet India**: Full list crawl and incremental updates for earnings transcripts.

## Features
- **Stealth Mode**: Uses Playwright with custom UA, viewport, and `webdriver` flag evasion to avoid detection.
- **Modular Architecture**: Separate logic for browser control (`browser_utils.py`) and HTML parsing (`page_parser.py`).
- **Incremental Updates**: Tracks already-scraped URLs to avoid redundant work.
- **Resumable**: Progress is saved to `progress.json` to allow resuming interrupted jobs.

## Setup
1. Install dependencies:
   ```powershell
   uv sync
   ```
2. One-time browser setup:
   ```powershell
   uv run playwright install chromium
   ```

## Usage
### AlphaStreet Scraper
```powershell
# Get help
uv run main.py --help

# Incremental update of transcripts list
uv run main.py --crawl-new

# Download individual transcript texts
uv run main.py --fetch-transcripts
```

## Repository Structure
- `main.py`: Entry point for the AlphaStreet scraper.
- `scraper.py`: Logic for fetching individual transcript pages.
- `browser_utils.py`: Shared Playwright utilities.
- `page_parser.py`: Shared HTML/text parsing utilities.
