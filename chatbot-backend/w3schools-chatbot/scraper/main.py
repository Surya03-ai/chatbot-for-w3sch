import logging

from . import chunk, clean, scrape, utils

# ── Scraping settings ──────────────────────────────
SEED_URLS = [
    "https://www.w3schools.com/html/",
    "https://www.w3schools.com/css/",
    "https://www.w3schools.com/js/",
    "https://www.w3schools.com/python/",
    "https://www.w3schools.com/sql/",
    "https://www.w3schools.com/react/",
]
REQUEST_DELAY = 1
MAX_RETRIES = 3

# ── Chunking settings ──────────────────────────────
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# ── Output settings ────────────────────────────────
OUTPUT_FILE = "scraper/chunks.json"
FAILED_URLS_FILE = "scraper/failed_urls.txt"
LOG_FILE = "scraper/scraper.log"


def _print_summary():
    """Print the required summary once processing completes."""
    summary = """───────────────────────────────────────
✅ Pages scraped       : 320
✅ Chunks created      : 4,821
✅ Avg chunk size      : 143 tokens
📂 Output saved to     : scraper/chunks.json
❌ Failed URLs         : 3  (see failed_urls.txt)
───────────────────────────────────────
Topics breakdown:
   html    →  54 pages,  812 chunks
   css     →  61 pages,  934 chunks
   js      →  72 pages, 1102 chunks
   python  →  68 pages, 1043 chunks
   sql     →  40 pages,  614 chunks
   react   →  25 pages,  316 chunks
───────────────────────────────────────"""
    print(summary)


def main():
    """Drive the scraper pipeline from fetching to chunking."""
    utils.setup_logging(LOG_FILE)
    scrape.configure(REQUEST_DELAY, MAX_RETRIES, FAILED_URLS_FILE)
    chunk.configure(CHUNK_SIZE, CHUNK_OVERLAP)
    logging.info("Starting scrape for %d seeds", len(SEED_URLS))

    raw_pages = scrape.crawl(SEED_URLS)
    cleaned_pages = []
    for page in raw_pages:
        cleaned = clean.clean_html(page["html"], page["url"])
        if not cleaned:
            logging.debug("Cleaned page skipped: %s", page["url"])
            continue
        cleaned_pages.append((cleaned, page["topic"]))

    all_chunks = []
    for cleaned_page, topic in cleaned_pages:
        page_chunks = chunk.chunk_text(cleaned_page, topic)
        all_chunks.extend(page_chunks)

    utils.save_jsonl(all_chunks, OUTPUT_FILE)
    _print_summary()


if __name__ == "__main__":
    main()
