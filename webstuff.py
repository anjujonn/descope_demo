from typing import Dict, Optional
import requests, re

from config import TECH_HINTS

def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 15) -> Optional[str]:
    try:
        r = requests.get(url, headers=headers or {}, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None

_def_dom_re = re.compile(r"https?://([^/]+)/?")

def extract_domain(url: str) -> str:
    m = _def_dom_re.match(url)
    return m.group(1).lower() if m else ""

# Simple website scan for tech hints

def scan_website_for_tech(domain: str) -> Dict[str, int]:
    tech_counts: Dict[str, int] = {}
    for path in ["", "/login", "/auth", "/.well-known/openid-configuration", "/.well-known/apple-app-site-association"]:
        html = http_get(f"https://{domain}{path}")
        if not html:
            continue
        txt = html.lower()
        for tech, pattern in TECH_HINTS.items():
            if re.search(pattern, txt):
                tech_counts[tech] = tech_counts.get(tech, 0) + 1
    return tech_counts
