import logging
import re
from typing import Dict

from bs4 import BeautifulSoup, Tag


def _extract_title(soup: BeautifulSoup, url: str) -> str:
    """Determine the best title candidate from the HTML."""
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    if soup.title and soup.title.string:
        return soup.title.get_text(strip=True)
    return url.rstrip("/").split("/")[-1] or url


def _remove_unwanted_elements(main: Tag):
    """Strip scripts, navigation, and other layout cruft from the main content."""
    for tag in main.find_all(["script", "style", "iframe", "noscript", "nav", "header", "footer"]):
        tag.decompose()
    class_keywords = ("w3-bar", "w3-top", "w3-sidebar", "w3-footer")
    id_keywords = ("topnav", "nav", "footer", "sidebar", "cookie", "ad", "banner")
    for tag in list(main.find_all(True)):
        classes = [cls.lower() for cls in (tag.get("class") or [])]
        if any(keyword in cls for cls in classes for keyword in class_keywords):
            tag.decompose()
            continue
        tag_id = (tag.get("id") or "").lower()
        if any(keyword in tag_id for keyword in id_keywords):
            tag.decompose()
    for tag in main.find_all(["div", "a"]):
        text = tag.get_text(" ", strip=True).lower()
        if "try it yourself" in text or "try it" in text:
            tag.decompose()


def _extract_code_blocks(main: Tag):
    """Replace code elements with placeholders so their content survives cleaning."""
    for tag in list(main.find_all(["pre", "code"])):
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
        placeholder = main.new_tag("div")
        placeholder["class"] = "example"
        placeholder["data-language"] = language
        placeholder.string = text
        tag.replace_with(placeholder)


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
    if not main_div:
        logging.warning("Missing div#main for %s", url)
        return {}
    _remove_unwanted_elements(main_div)
    _extract_code_blocks(main_div)
    text = _cleanup_text(main_div.get_text("\n"))
    return {"title": title, "text": text, "url": url}
