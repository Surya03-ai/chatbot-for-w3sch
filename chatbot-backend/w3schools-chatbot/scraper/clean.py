import logging
import re
from typing import Dict

from bs4 import BeautifulSoup, Tag, NavigableString


def _extract_title(soup: BeautifulSoup, url: str) -> str:
    """Determine the best title candidate from the HTML.

    W3Schools often splits headings into adjacent inline children
    (e.g. <h1>HTML<span>Attributes</span></h1>) which can create
    concatenated words when using get_text(strip=True) without
    a separator.
    """
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        # Use separator=" " to preserve word boundaries between children
        title = h1.get_text(separator=" ", strip=True)
        # Collapse repeated spaces into single spaces
        title = re.sub(r" +", " ", title).strip()
        # Fix missing boundary between uppercase acronym and TitleCase word
        # e.g. "HTMLAttributes" -> "HTML Attributes"
        title = re.sub(r"([A-Z]{2,})([A-Z][a-z])", r"\1 \2", title)
        # Fix missing boundary between lower and upper case transitions
        # e.g. "JavaScriptJSON" -> "JavaScript JSON"
        title = re.sub(r"([a-z])([A-Z])", r"\1 \2", title)
        return title
    if soup.title and soup.title.string:
        title = soup.title.get_text(separator=" ", strip=True)
        title = re.sub(r" +", " ", title).strip()
        return title
    return url.rstrip("/").split("/")[-1] or url


def _remove_unwanted_elements(main: Tag):
    """Strip scripts, navigation, and other layout cruft from the main content."""
    for tag in main.find_all(["script", "style", "iframe", "noscript", "nav", "header", "footer"]):
        tag.decompose()
    class_keywords = ("w3-bar", "w3-top", "w3-sidebar", "w3-footer")
    id_keywords = ("topnav", "nav", "footer", "sidebar", "cookie", "ad", "banner")
    for tag in list(main.find_all(True)):
        try:
            if not isinstance(tag, Tag):
                continue
            if not tag.attrs:
                continue
            classes = [cls.lower() for cls in (tag.get("class") or [])]
            if any(keyword in cls for cls in classes for keyword in class_keywords):
                tag.decompose()
                continue
            tag_id = (tag.get("id") or "").lower()
            if any(keyword in tag_id for keyword in id_keywords):
                tag.decompose()
        except Exception:
            continue
    JUNK_PHRASES = (
        "try it yourself",
        "try it",
        "sign in to track",
        "track your progress",
        "sign up",
        "get certified",
        "kickstart your career",
        "learning by examples",
        "html quiz",
        "html exercises",
        "css quiz",
        "css exercises",
        "js quiz",
        "js exercises",
        "python quiz",
        "python exercises",
        "sql quiz",
        "sql exercises",
        "react quiz",
        "react exercises",
        "video:",
        "get your own",
        "create your own",
        "upgrade your learning",
        "w3schools account",
        "leaderboard",
        "daily streaks",
    )
    for tag in list(main.find_all(["div", "a", "p", "section"])):
        try:
            text = tag.get_text(" ", strip=True).lower()
            if any(phrase in text for phrase in JUNK_PHRASES):
                tag.decompose()
        except Exception:
            continue


def _extract_code_blocks(main_div: Tag):
    """Replace code elements with placeholders so their content survives cleaning."""
    if main_div is None:
        return
    for tag in list(main_div.find_all(["pre", "code"])):
        text = tag.get_text("\n", strip=True)
        if not text:
            tag.decompose()
            continue
        classes = [cls.lower() for cls in (tag.get("class") or [])]
        language = "code"
        for cls in classes:
            if cls.startswith("language-"):
                language = cls.split("-", 1)[1]
                break
            if cls in {"w3-code", "code"}:
                continue
            if cls.endswith("high"):
                language = cls.replace("high", "").strip()
                break
        placeholder = Tag(name="div")
        placeholder["class"] = "example"
        placeholder["data-language"] = language
        placeholder.string = text
        tag.replace_with(placeholder)


def _remove_navigation_symbols(text: str) -> str:
    """
    Remove navigation arrows, rating symbols, and other
    non-content characters from cleaned text.
    Removes:
        ❮ Previous   Next ❯
        ❮ Home       Next ❯  
        ★  +1
        🏁  and other emoji
    """
    # Remove navigation arrow lines
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are only navigation/symbols
        if stripped in ("❮ Previous", "Next ❯", "❮ Home",
                        "★", "+1", "🏁", "❮", "❯"):
            continue
        # Skip lines containing only arrows and whitespace
        if all(c in "❮❯★+0123456789 \t" for c in stripped) and stripped:
            continue
        # Skip lines with navigation pattern
        if ("❮" in stripped and "previous" in stripped.lower()):
            continue
        if ("❯" in stripped and "next" in stripped.lower()):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _cleanup_text(text: str) -> str:
    """Normalize whitespace, collapse blank lines, and trim the result."""
    lines = text.splitlines()
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append("")
            continue
        blank_count = 0
        cleaned_lines.append(stripped)
    cleaned = "\n".join(cleaned_lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def clean_html(html: str, url: str) -> Dict[str, str]:
    """Clean a W3Schools tutorial page and return its title and text."""
    soup = BeautifulSoup(html, "lxml")
    title = _extract_title(soup, url)
    main_div = soup.find("div", id="main")
    if main_div is None:
        logging.warning(f"No div#main found for {url}, skipping")
        return {"title": "", "text": "", "url": url}
    _remove_unwanted_elements(main_div)
    _extract_code_blocks(main_div)
    raw_text = main_div.get_text("\n")
    text = _cleanup_text(raw_text)
    text = _remove_navigation_symbols(text)
    return {"title": title, "text": text, "url": url}
