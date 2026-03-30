import logging
import random
import time
from collections import deque
from typing import Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.utils import write_failed_url

REQUEST_DELAY = 1.0
MAX_RETRIES = 3
FAILED_URLS_FILE = "scraper/failed_urls.txt"

_ALLOWED_PREFIXES = (
    "/html/html_",
    "/css/css_",
    "/js/js_",
    "/python/python_",
    "/sql/sql_",
    "/react/react_",
)
_EXCLUDE_KEYWORDS = ("tryit", "exercise", "quiz", "bootcamp", "game", "certificate")
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
    return any(path.startswith(prefix) for prefix in _ALLOWED_PREFIXES)


def _get_topic_from_path(path: str) -> str:
    """Extract the topic slug from a tutorial path."""
    parts = path.strip("/").split("/", 1)
    return parts[0] if parts else ""


def crawl(seed_urls: list) -> list[Dict]:
    """Crawl seed URLs and gather tutorial pages that match the allowed patterns."""
    queue = deque(seed_urls)
    seen = set(seed_urls)
    scraped = []
    with tqdm(desc="Scraping W3Schools", unit="page") as pbar:
        while queue:
            url = queue.popleft()
            html = fetch_page(url)
            pbar.update(1)
            if html:
                parsed_source = urlparse(url)
                topic = _get_topic_from_path(parsed_source.path)
                if any(parsed_source.path.lower().startswith(prefix) for prefix in _ALLOWED_PREFIXES):
                    scraped.append({"url": url, "html": html, "topic": topic})
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
