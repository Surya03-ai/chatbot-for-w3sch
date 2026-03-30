import json
import logging
import os
from pathlib import Path

import tiktoken

_encoding = tiktoken.get_encoding("cl100k_base")


def setup_logging(log_file: str):
    """Configure console/file logging so INFO+ appears on stdout and DEBUG+ is saved.

    Args:
        log_file: Path of the file that receives verbose logs.
    """
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.handlers = []
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def count_tokens(text: str) -> int:
    """Return the number of cl100k_base tokens in the supplied text.

    Args:
        text: Input string that should be tokenized.

    Returns:
        The token count as an integer.
    """
    return len(_encoding.encode(text or ""))


def save_jsonl(data: list[dict], filepath: str):
    """Persist a JSONL dataset to disk and log the record count.

    Args:
        data: List of dictionaries to serialize.
        filepath: Target JSONL file path.
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        for record in data:
            fh.write(json.dumps(record, ensure_ascii=False) + os.linesep)
    logging.info("Saved %d records to %s", len(data), filepath)


def load_jsonl(filepath: str) -> list:
    """Read a JSONL file into a list of dictionaries; missing file → empty list.

    Args:
        filepath: JSONL file to read.

    Returns:
        List of decoded JSON objects.
    """
    if not Path(filepath).exists():
        logging.debug("JSONL file %s not found, returning empty list", filepath)
        return []
    records = []
    with open(filepath, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            records.append(json.loads(stripped))
    logging.info("Loaded %d records from %s", len(records), filepath)
    return records


def write_failed_url(url: str, filepath: str):
    """Append a single failed URL to the failure log so it can be retried later.

    Args:
        url: Page URL that failed after retries.
        filepath: Failed URL log path.
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as fh:
        fh.write(url + os.linesep)
    logging.debug("Recorded failed URL %s", url)
