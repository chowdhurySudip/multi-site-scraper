import re
from bs4 import BeautifulSoup

def annotate_links(soup):
    """Rewrites anchor tags as 'text [href]' in-place to preserve link info in text dumps."""
    for a in soup.find_all('a', href=True):
        link_text = a.get_text(strip=True)
        if link_text:
            a.string = f"{link_text} [{a['href']}]"

def has_next_page(soup):
    """Checks if there's a 'Next' pagination link."""
    return any('Next' in str(a) for a in soup.find_all('a'))

def build_page_url(page_num):
    """Constructs the AlphaStreet listing URL for a given page number."""
    base_url = "https://alphastreet.com/india/category/transcripts/"
    if page_num == 1:
        return base_url
    return f"{base_url}page/{page_num}"

def is_valid_transcript_url(link):
    """Returns True if the link is likely a transcript/article, not a category/home link."""
    prefix = 'https://alphastreet.com/india/'
    return link.startswith(prefix) and '/category/' not in link and len(link) > len(prefix)

def parse_entry(lines, index):
    """Parses an annotated line and its surroundings into an entry dict."""
    line = lines[index]
    match = re.match(r'^(.*?)\s*\[(.*?)\]$', line)
    if not match:
        return None
        
    text = match.group(1).strip()
    link = match.group(2).strip()
    
    if not is_valid_transcript_url(link):
        return None
        
    date = ""
    # Look ahead for date marker '●' then the date string
    if index + 2 < len(lines) and lines[index+1].strip() == '●':
        date = lines[index+2].strip()
        
    article_type = 'Transcript' if 'transcript' in text.lower() else 'Article'
    
    return {
        'Transcript': text,
        'Date': date,
        'Link': link,
        'Type': article_type
    }
