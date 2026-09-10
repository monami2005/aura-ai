import os
import re
import urllib.parse
from typing import List, Optional
import requests
from dotenv import load_dotenv
from .models import WebSearchResultItem

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
REQUEST_TIMEOUT = 5.0  # seconds
MAX_RESULTS = 5
MAX_BODY_BYTES = 500_000  # 500 KB response limit

HEADERS = {
    "User-Agent": "AURA-AI-Assistant/1.0 (Desktop Intelligence Core; +https://aura.ai)"
}

def validate_and_sanitize_url(raw_url: Optional[str]) -> Optional[str]:
    if not raw_url or not isinstance(raw_url, str):
        return None
    url_clean = raw_url.strip()
    if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
        return None
    return url_clean

def extract_domain(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or "web-source"
    except Exception:
        return "web-source"

def search_tavily(query: str) -> List[WebSearchResultItem]:
    """Real retrieval using Tavily Search API if configured."""
    if not TAVILY_API_KEY:
        return []
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": MAX_RESULTS,
            "include_domains": [],
            "exclude_domains": []
        }
        res = requests.post(url, json=payload, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if res.status_code == 200:
            data = res.json()
            items: List[WebSearchResultItem] = []
            for item in data.get("results", []):
                val_url = validate_and_sanitize_url(item.get("url"))
                if not val_url:
                    continue
                title = str(item.get("title", "")).strip() or "Web Source"
                snippet = str(item.get("content", "")).strip() or "No snippet available."
                domain = extract_domain(val_url)
                items.append(
                    WebSearchResultItem(
                        title=title[:120],
                        url=val_url,
                        domain=domain,
                        snippet=snippet[:400],
                        published_date=item.get("published_date")
                    )
                )
            return items
    except Exception:
        pass
    return []

def search_duckduckgo_open(query: str) -> List[WebSearchResultItem]:
    """Real retrieval using DuckDuckGo Instant Answer / Open Search API (No key required)."""
    try:
        endpoint = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        res = requests.get(endpoint, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if res.status_code == 200 and len(res.content) <= MAX_BODY_BYTES:
            data = res.json()
            items: List[WebSearchResultItem] = []
            
            # 1. Primary abstract result
            abstract = data.get("AbstractText", "").strip()
            abstract_url = validate_and_sanitize_url(data.get("AbstractURL"))
            abstract_source = data.get("AbstractSource", "").strip()
            
            if abstract and abstract_url:
                items.append(
                    WebSearchResultItem(
                        title=f"{abstract_source or 'DuckDuckGo'}: {data.get('Heading', query)}",
                        url=abstract_url,
                        domain=extract_domain(abstract_url),
                        snippet=abstract[:400],
                        published_date="Live Index"
                    )
                )

            # 2. Related topics
            for topic in data.get("RelatedTopics", [])[:MAX_RESULTS]:
                if isinstance(topic, dict) and "FirstURL" in topic and "Text" in topic:
                    t_url = validate_and_sanitize_url(topic.get("FirstURL"))
                    t_text = topic.get("Text", "").strip()
                    if t_url and t_text:
                        items.append(
                            WebSearchResultItem(
                                title=t_text.split(" - ")[0][:90] if " - " in t_text else query[:60],
                                url=t_url,
                                domain=extract_domain(t_url),
                                snippet=t_text[:350],
                                published_date="Live Index"
                            )
                        )
            if items:
                return items[:MAX_RESULTS]
    except Exception:
        pass
    return []

def search_wikipedia_rest(query: str) -> List[WebSearchResultItem]:
    """Real retrieval using Wikipedia OpenSearch API (No key required)."""
    try:
        endpoint = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": "1",
            "srlimit": str(MAX_RESULTS)
        }
        res = requests.get(endpoint, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if res.status_code == 200 and len(res.content) <= MAX_BODY_BYTES:
            data = res.json()
            search_results = data.get("query", {}).get("search", [])
            items: List[WebSearchResultItem] = []
            for entry in search_results:
                title = entry.get("title", "").strip()
                page_id = entry.get("pageid")
                raw_snippet = entry.get("snippet", "")
                clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
                article_url = f"https://en.wikipedia.org/?curid={page_id}" if page_id else f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                
                items.append(
                    WebSearchResultItem(
                        title=title,
                        url=article_url,
                        domain="en.wikipedia.org",
                        snippet=clean_snippet[:350] or f"Information regarding {title}.",
                        published_date=entry.get("timestamp", "").split("T")[0] if "timestamp" in entry else "Recent"
                    )
                )
            if items:
                return items
    except Exception:
        pass
    return []

def perform_safe_web_search(query: str) -> List[WebSearchResultItem]:
    """
    Main Real Outbound Web Search Pipeline.
    Prioritizes real providers and performs real outbound HTTP requests.
    Guarantees prompt-injection safety by treating all retrieved content
    as passive, untrusted string data.
    Returns empty list if external web is unreachable.
    """
    clean_q = query.strip()
    if not clean_q:
        return []

    # 1. Try Tavily Search API if configured
    if TAVILY_API_KEY:
        tavily_results = search_tavily(clean_q)
        if tavily_results:
            return tavily_results

    # 2. Try DuckDuckGo Open Search API
    ddg_results = search_duckduckgo_open(clean_q)
    if ddg_results:
        return ddg_results

    # 3. Try Wikipedia OpenSearch REST API
    wiki_results = search_wikipedia_rest(clean_q)
    if wiki_results:
        return wiki_results

    # External providers unreachable or returned zero results
    return []
