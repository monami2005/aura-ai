import webbrowser
import urllib.parse
from typing import Dict, Any, Tuple, Optional

BLOCKED_DOMAINS_FOR_AUTOMATION = [
    "paypal.com",
    "stripe.com",
    "chase.com",
    "bankofamerica.com",
    "wellsfargo.com",
    "login.live.com",
    "accounts.google.com"
]

def sanitize_url(raw_url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate and sanitize user-provided URLs.
    Ensures safe HTTP/HTTPS protocols and prevents protocol-level exploits.
    """
    if not raw_url or not str(raw_url).strip():
        return False, None, "URL cannot be empty."

    url = raw_url.strip()
    
    # Block dangerous protocols
    for scheme in ("javascript:", "file:", "data:", "vbscript:", "blob:"):
        if url.lower().startswith(scheme):
            return False, None, f"Dangerous URL scheme '{scheme}' is strictly blocked."

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            return False, None, f"Invalid URL format: '{raw_url}'"

        domain = parsed.netloc.lower()
        if any(blocked in domain for blocked in BLOCKED_DOMAINS_FOR_AUTOMATION):
            return False, None, f"Automated interactions on sensitive banking or authentication service '{domain}' are blocked for security."

        return True, url, None
    except Exception as e:
        return False, None, f"URL parse error: {str(e)}"


def safe_open_url(url: str) -> Dict[str, Any]:
    valid, clean_url, err = sanitize_url(url)
    if not valid or not clean_url:
        return {"success": False, "error": err}

    try:
        webbrowser.open(clean_url)
        return {
            "success": True,
            "result": f"Opened website: {clean_url}",
            "url": clean_url
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open browser: {str(e)}"}


def safe_browser_search(query: str, engine: str = "google") -> Dict[str, Any]:
    if not query or not query.strip():
        return {"success": False, "error": "Search query cannot be empty."}

    encoded = urllib.parse.quote_plus(query.strip())
    engines = {
        "google": f"https://www.google.com/search?q={encoded}",
        "duckduckgo": f"https://duckduckgo.com/?q={encoded}",
        "bing": f"https://www.bing.com/search?q={encoded}"
    }
    target_url = engines.get(engine.lower(), engines["google"])

    try:
        webbrowser.open(target_url)
        return {
            "success": True,
            "result": f"Dispatched browser search for '{query}' on {engine.capitalize()}.",
            "url": target_url,
            "query": query
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open browser search: {str(e)}"}


def safe_launch_browser(app_name: str = "chrome") -> Dict[str, Any]:
    from ..actions import ALLOWED_APPLICATIONS
    # Check if registered or open default browser
    key = app_name.lower().strip()
    if key in ("chrome", "google chrome"):
        target_url = "https://www.google.com"
    else:
        target_url = "https://www.google.com"

    try:
        webbrowser.open(target_url)
        return {
            "success": True,
            "result": f"Browser opened successfully to {target_url}.",
            "url": target_url
        }
    except Exception as e:
        return {"success": False, "error": f"Could not launch browser: {str(e)}"}
