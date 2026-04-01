import json
import logging
import os
import random
import time
from collections import deque
from datetime import datetime
from typing import Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper import clean
from scraper.utils import write_failed_url

REQUEST_DELAY = 1.0
MAX_RETRIES = 3
FAILED_URLS_FILE = "scraper/failed_urls.txt"
RAW_HTML_DIR = "scraper/raw_html"

_ALLOWED_PREFIXES = (
    "/html/html_",
    "/css/css_",
    "/js/js_",
    "/python/python_",
    "/sql/sql_",
    "/react/react_",
)
_EXCLUDE_PREFIXES = (
    "/html/html_ref",
    "/css/css_ref",
    "/js/js_ref",
    "/python/python_ref",
    "/sql/sql_ref",
    "/react/react_ref",
    "/html/html_challenge",
    "/css/css_challenge",
    "/js/js_challenge",
    "/python/python_challenge",
    "/sql/sql_challenge",
    "/react/react_challenge",
)
_EXCLUDE_KEYWORDS = ("tryit", "exercise", "quiz", "bootcamp", "game", "certificate", "challenges", "ref_", "reference", "_ref", "default")
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
)


def configure(request_delay: float, max_retries: int, failed_urls_file: str):
    """Update module-level settings from the main configuration."""
    global REQUEST_DELAY, MAX_RETRIES, FAILED_URLS_FILE
    REQUEST_DELAY = request_delay
    MAX_RETRIES = max_retries
    FAILED_URLS_FILE = failed_urls_file


def save_raw_page(url: str, html: str, topic: str) -> None:
    """
    Fetch HTML, clean it immediately using clean.py, and save
    structured readable data to disk instead of raw HTML.
    
    Each saved JSON file contains:
        url        — the page URL
        topic      — html/css/js/python/sql/react
        title      — H1 heading of the page
        text       — cleaned readable text with code blocks
        scraped_at — ISO timestamp of when it was scraped
    
    File is saved to scraper/raw_html/<slug>.json
    """
    os.makedirs(RAW_HTML_DIR, exist_ok=True)

    # Clean HTML immediately — no raw HTML stored
    cleaned = clean.clean_html(html, url)

    # Build structured data
    data = {
        "url": url,
        "topic": topic,
        "title": cleaned["title"],
        "text": cleaned["text"],
        "scraped_at": datetime.now().isoformat(timespec="seconds")
    }

    # Convert URL to safe filename
    slug = url.replace("https://www.w3schools.com/", "")
    slug = slug.replace("/", "__").replace(".asp", "").strip("_")
    filepath = os.path.join(RAW_HTML_DIR, f"{slug}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logging.debug("Saved cleaned page: %s", filepath)


def already_scraped(url: str) -> bool:
    """Return True if the URL already has a saved raw HTML file."""
    slug = url.replace("https://www.w3schools.com/", "")
    slug = slug.replace("/", "__").replace(".asp", "")
    slug = slug.strip("_")
    filepath = os.path.join(RAW_HTML_DIR, f"{slug}.json")
    return os.path.exists(filepath)


def fetch_page(url: str) -> str | None:
    """Retrieve a page, respecting retry logic and logging failures."""
    headers = {"User-Agent": _USER_AGENT}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            logging.warning("Attempt %d failed for %s: %s", attempt, url, exc)
            if attempt < MAX_RETRIES:
                time.sleep(2)
    logging.error("All retries exhausted for %s", url)
    write_failed_url(url, FAILED_URLS_FILE)
    return None


def _is_valid_link(parsed) -> bool:
    """Determine if the parsed URL is an internal tutorial page."""
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc.endswith("w3schools.com"):
        return False
    path = parsed.path.lower()
    if "#" in parsed.fragment:
        return False
    if any(bad in path for bad in _EXCLUDE_KEYWORDS):
        return False
    if any(path.startswith(prefix) for prefix in _EXCLUDE_PREFIXES):
        return False
    return any(path.startswith(prefix) for prefix in _ALLOWED_PREFIXES)


def _get_topic_from_path(path: str) -> str:
    """Extract the topic slug from a tutorial path."""
    parts = path.strip("/").split("/", 1)
    return parts[0] if parts else ""


def load_saved_pages() -> list[dict]:
    """Load all previously scraped pages from scraper/raw_html/ for cleaning.

    Each JSON file under RAW_HTML_DIR should contain keys: url, html, topic.
    """
    pages = []
    if not os.path.exists(RAW_HTML_DIR):
        logging.warning("raw_html/ folder not found, nothing to load")
        return pages
    files = [f for f in os.listdir(RAW_HTML_DIR) if f.endswith(".json")]
    for filename in files:
        filepath = os.path.join(RAW_HTML_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            pages.append(json.load(f))
    logging.info(f"Loaded {len(pages)} saved pages from raw_html/")
    return pages


def crawl(seed_urls: list, limit: int = None) -> list[Dict]:
    """Crawl seed URLs and gather tutorial pages that match the allowed patterns.
    
    Args:
        seed_urls: List of starting URLs to crawl from
        limit: Optional limit on number of pages to scrape before stopping
    """
    queue = deque(seed_urls)
    seen = set(seed_urls)
    scraped = []

    with tqdm(desc="Scraping W3Schools", unit="page") as pbar:
        while queue:
            url = queue.popleft()
            parsed_source = urlparse(url)
            topic = _get_topic_from_path(parsed_source.path)
            pbar.update(1)

            # Check if limit reached
            if limit is not None and len(scraped) >= limit:
                logging.info("Test limit %d reached, stopping.", limit)
                break

            # Step 1: Get HTML — from disk or from web
            html = None
            if already_scraped(url):
                logging.info("Already scraped, loading from disk: %s", url)
                slug = url.replace("https://www.w3schools.com/", "")
                slug = slug.replace("/", "__").replace(".asp", "").strip("_")
                filepath = os.path.join(RAW_HTML_DIR, f"{slug}.json")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                    # Handle both old format (with "html" key) and new format (with "text" key)
                    if "text" in saved:
                        # New format — already cleaned
                        # For link discovery we need original HTML, which we don't have
                        # Skip link discovery for this page
                        html = None
                    elif "html" in saved:
                        # Old format — has raw HTML, clean it now and resave
                        html = saved["html"]
                        save_raw_page(url, html, topic)  # resave in new format
                except Exception as e:
                    logging.warning("Failed to load saved page %s: %s", url, e)
            else:
                html = fetch_page(url)
                if html:
                    path = parsed_source.path.lower()
                    
                    # Check if this is an actual tutorial page
                    is_tutorial = any(
                        path.startswith(prefix) 
                        for prefix in _ALLOWED_PREFIXES
                    )
                    
                    # Check if this is a reference or challenge page
                    is_excluded = any(
                        path.startswith(prefix)
                        for prefix in _EXCLUDE_PREFIXES
                    )
                    
                    # Only save actual tutorial pages
                    if is_tutorial and not is_excluded:
                        save_raw_page(url, html, topic)
                        scraped.append({
                            "url": url,
                            "html": html,
                            "topic": topic
                        })

            # Step 2: Discover links — runs for BOTH saved and new pages
            if html:
                soup = BeautifulSoup(html, "lxml")
                for anchor in soup.find_all("a", href=True):
                    href = anchor["href"]
                    if "#" in href:
                        continue
                    absolute = urljoin(url, href)
                    parsed = urlparse(absolute)
                    if not _is_valid_link(parsed):
                        continue
                    if absolute in seen:
                        continue
                    seen.add(absolute)
                    queue.append(absolute)

            delay = REQUEST_DELAY + random.uniform(-0.2, 0.2)
            time.sleep(max(0, delay))

    return scraped