from bs4 import BeautifulSoup
from webstuff import http_get


class HyperPersonalizationAgent:
    def recent_hook(self, domain: str) -> str:
        # Try a /blog or /news page and grab latest title
        for path in ["/blog", "/news", "/changelog"]:
            html = http_get(f"https://{domain}{path}")
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            h = soup.find(["h1", "h2", "h3"])
            if h and h.get_text(strip=True):
                return f"Saw your recent post: '{h.get_text(strip=True)}' — congrats on the launch."
        return ""
