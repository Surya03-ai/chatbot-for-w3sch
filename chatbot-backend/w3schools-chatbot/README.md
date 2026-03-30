# W3Schools RAG Scraper (Phase 1)

This project scrapes W3Schools tutorials, cleans the HTML, and chunks the text for embedding ingestion.

## Structure

```
w3schools-chatbot/
├── scraper/
│   ├── main.py      # orchestrates the pipeline
│   ├── scrape.py    # fetches pages and follows tutorial links
│   ├── clean.py     # strips layout, scripts, and retains code examples
│   ├── chunk.py     # token-aware chunking using langchain/tiktoken
│   ├── utils.py     # logging, token counting, JSONL helpers
├── requirements.txt  # pinned dependencies
├── README.md         # this file
```

## Running

```bash
python scraper/main.py
```

All settings (seed URLs, delays, chunk size, output paths, etc.) are defined at the top of `scraper/main.py`.

## Output

- `scraper/chunks.json` is JSON Lines (one object per line) ready for Phase 2 vector embedding.
- `scraper/failed_urls.txt` records any URLs that failed after retries.
- `scraper/scraper.log` captures pipeline logging with INFO+ output on the console and DEBUG output in the file.
