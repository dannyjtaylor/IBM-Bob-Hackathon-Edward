"""
Edward Web Tools — real web search and page scraping, no API key required.
Search:   ddgs (DuckDuckGo, free, no key needed)
Scraping: requests + BeautifulSoup
"""

import re
import urllib.parse
from typing import Optional

from logger import get_logger

logger = get_logger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT = 9


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search DuckDuckGo via the ddgs library and return formatted text results.
    Falls back gracefully if the package isn't installed.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return f"[Web search unavailable — run: pip install ddgs]\n\nTo search manually: https://duckduckgo.com/?q={urllib.parse.quote(query)}"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: {query}"

        lines = [f'Search results for "{query}":\n']
        for i, r in enumerate(results, 1):
            title = r.get("title", "").strip()
            body  = r.get("body", "").strip()
            href  = r.get("href", "").strip()
            lines.append(f"{i}. **{title}**")
            if body:
                lines.append(f"   {body}")
            if href:
                lines.append(f"   {href}")
            lines.append("")

        return "\n".join(lines).strip()

    except Exception as e:
        logger.error(f"web_search failed: {e}")
        return f"Web search failed: {e}\n\nTry: https://duckduckgo.com/?q={urllib.parse.quote(query)}"


def fetch_page_text(url: str, max_chars: int = 4000) -> str:
    """
    Fetch a web page and return its readable text content (no HTML).
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return "[Page fetch — run: pip install requests beautifulsoup4]"

    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s{2,}", " ", text).strip()

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n… [truncated — {len(text):,} chars total]"

        return text or "(Page appears empty)"

    except Exception as e:
        logger.error(f"fetch_page_text({url}): {e}")
        return f"Could not fetch page: {e}"


def get_page_title(url: str) -> Optional[str]:
    """Quick title-only fetch."""
    try:
        import requests
        from bs4 import BeautifulSoup

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        resp = requests.get(url, headers=_HEADERS, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        tag  = soup.find("title")
        return tag.get_text(strip=True) if tag else None
    except Exception:
        return None
