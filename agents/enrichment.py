from bs4 import BeautifulSoup
from storage import Storage
from typing import List
import time

from webstuff import http_get, extract_domain, scan_website_for_tech

class EnrichmentAgent:
    def __init__(self, storage: Storage):
        self.storage = storage

    def _guess_careers(self, domain: str) -> List[str]:
        roles = []
        for path in ["/careers", "/jobs", "/about", "/team"]:
            html = http_get(f"https://{domain}{path}")
            if not html:
                continue
            text = BeautifulSoup(html, "html.parser").get_text(" ").lower()
            for role in ["security", "identity", "backend", "platform", "mobile", "sre", "devops"]:
                if role in text:
                    roles.append(role)
        return sorted(set(roles))

    def _size_hint(self, domain: str) -> str:
        # infer size by number of employees visible on team page
        html = http_get(f"https://{domain}/team") or http_get(f"https://{domain}/about")
        if not html:
            return "unknown"
        # naive heuristic -> count occurrences of common job titles as a proxy
        text = BeautifulSoup(html, "html.parser").get_text(" ").lower()
        count = 0
        for kw in ["engineer", "product", "sales", "marketing", "designer", "finance", "hr"]:
            count += text.count(kw)
        if count > 200: return ">1000"
        if count > 80: return "251-1000"
        if count > 30: return "51-250"
        if count > 10: return "11-50"
        if count > 3: return "2-10"
        return "1"

    def run(self):
        signals = self.storage.fetch_signals(limit=100)
        for s in signals:
            domain = s.get("detected_domain") or extract_domain(s.get("url", ""))
            if not domain:
                continue
            tech_hints = scan_website_for_tech(domain)
            roles = self._guess_careers(domain)
            size = self._size_hint(domain)
            self.storage.upsert_enrichment(signal_url=s["url"], domain=domain,
                                           tech_hints=tech_hints, company_size_hint=size,
                                           hiring_roles=roles)
            time.sleep(0.3)
