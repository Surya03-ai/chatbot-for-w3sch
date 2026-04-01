import logging

from tqdm import tqdm

from . import chunk, clean, scrape, utils

# ── Scraping settings ──────────────────────────────
SEED_URLS = [
    "https://www.w3schools.com/html/",
    "https://www.w3schools.com/css/",
    "https://www.w3schools.com/js/",
    "https://www.w3schools.com/python/",
    "https://www.w3schools.com/sql/",
    "https://www.w3schools.com/react/"
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

# ── Test mode settings ─────────────────────────────
# TEST_MODE = True
TEST_MODE = False
TEST_PAGE_LIMIT = 10
TEST_OUTPUT = "scraper/chunks_test.json"


def main():
    """Drive the scraper pipeline from fetching to chunking."""
    utils.setup_logging(LOG_FILE)
    scrape.configure(REQUEST_DELAY, MAX_RETRIES, FAILED_URLS_FILE)
    chunk.configure(CHUNK_SIZE, CHUNK_OVERLAP)
    logging.info("Starting scrape for %d seeds", len(SEED_URLS))

    # Step 1: scrape + clean + save in one step
    limit = TEST_PAGE_LIMIT if TEST_MODE else None
    scrape.crawl(SEED_URLS, limit=limit)

    # Step 2: load all cleaned pages from disk
    pages = scrape.load_saved_pages()
    logging.info("Total pages loaded: %d", len(pages))

    # Step 3: chunk directly, no clean step needed
    all_chunks = []
    failed = 0
    for page in tqdm(pages, desc="Chunking pages"):
        try:
            if not page.get("text", "").strip():
                failed += 1
                continue
            chunks = chunk.chunk_text(page, page["topic"])
            all_chunks.extend(chunks)
        except Exception as e:
            logging.error("Failed to chunk %s: %s", page["url"], e)
            failed += 1
            continue

    # Step 4: save chunks
    output_file = TEST_OUTPUT if TEST_MODE else OUTPUT_FILE
    utils.save_jsonl(all_chunks, output_file)

    # Step 5: print summary
    if TEST_MODE:
        # Test mode: detailed report
        print("═" * 47)
        print("TEST REPORT")
        print("═" * 47)
        print(f"Pages scraped     : {len(pages)}")
        print(f"Chunks created    : {len(all_chunks)}")
        
        # Calculate avg tokens per chunk
        total_tokens = sum(ch["metadata"]["token_count"] for ch in all_chunks) if all_chunks else 0
        avg_tokens = total_tokens / len(all_chunks) if all_chunks else 0
        print(f"Avg tokens/chunk  : {avg_tokens:.1f}")
        print(f"Output file       : {output_file}")
        
        print("═" * 47)
        print("Page list:")
        for page in pages:
            topic = page.get("topic", "unknown").upper()
            title = page.get("title", "Untitled")
            url = page.get("url", "")
            print(f"[{topic}] {title} — {url}")
        
        print("═" * 47)
        if all_chunks:
            first_chunk = all_chunks[0]
            preview_text = first_chunk["text"][:200].replace("\n", " ")
            print("First chunk preview:")
            print(f"URL   : {first_chunk['metadata']['source_url']}")
            print(f"Title : {first_chunk['metadata']['page_title']}")
            print(f"Text  : {preview_text}...")
        print("═" * 47)
        print("✅ If looks correct set TEST_MODE=False for full run")
    else:
        # Production mode: simple report
        print("─" * 48)
        print(f"✅ Pages loaded        : {len(pages)}")
        print(f"✅ Chunks created      : {len(all_chunks)}")
        print(f"❌ Pages skipped       : {failed}")
        print(f"📂 Output saved to     : {output_file}")
        print("─" * 48)


if __name__ == "__main__":
    main()
