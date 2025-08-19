import feedparser
import time
from typing import List, Tuple

from bs4 import BeautifulSoup
import requests
from config import AUTH_KEYWORDS
from storage import Storage
from webstuff import extract_domain


class SignalDetectionAgent:
    """NOTE: 
        Sources implemented:
        - GitHub issues search (unauthenticated; low rate limit)
        - Hacker News Algolia search API
        - RSS feeds (security / engineering blogs)
    """
    def __init__(self, storage: Storage):
        self.storage = storage

    def _github_search(self, q: str, per_page: int = 5) -> List[Tuple[str, str, str]]:
        url = f"https://api.github.com/search/issues?q={requests.utils.quote(q)}&per_page={per_page}&sort=updated"
        try:
            data = requests.get(url, timeout=20).json()
            items = data.get("items", [])
        except Exception:
            items = []
        out = []
        for it in items:
            title = it.get("title", "")
            html_url = it.get("html_url", "")
            snippet = (it.get("body") or "")[:300]
            out.append((html_url, title, snippet))
        return out

    def _hn_search(self, q: str, hits: int = 5) -> List[Tuple[str, str, str]]:
        url = f"https://hn.algolia.com/api/v1/search?query={requests.utils.quote(q)}&tags=story"
        try:
            data = requests.get(url, timeout=20).json()
            items = data.get("hits", [])[:hits]
        except Exception:
            items = []
        out = []
        for it in items:
            title = it.get("title", "")
            url = it.get("url") or f"https://news.ycombinator.com/item?id={it.get('objectID')}"
            snippet = title
            out.append((url, title, snippet))
        return out

    def _rss_pull(self, feed_url: str, limit: int = 5) -> List[Tuple[str, str, str]]:
        try:
            d = feedparser.parse(feed_url)
        except Exception:
            return []
        out = []
        for entry in d.entries[:limit]:
            url = entry.link
            title = entry.title
            summary = BeautifulSoup(getattr(entry, "summary", ""), "html.parser").get_text()[:300]
            out.append((url, title, summary))
        return out

    def run(self):
        queries = [
            "auth0 migration", "okta outage", "SAML SSO problem", "OIDC error", "MFA rollout issue",
            "passwordless login broken", "oauth callback error"
        ]
        # GitHub & HN
        for q in queries:
            for url, title, snippet in self._github_search(q):
                # print(f'Github: {url, title,snippet}\n')
                self.storage.upsert_signal(
                    source="github", url=url, title=title, snippet=snippet,
                    detected_company="", detected_domain=extract_domain(url)
                )
            time.sleep(0.5)
            for url, title, snippet in self._hn_search(q):
                # print(f'HN: {url, title,snippet}\n')
                self.storage.upsert_signal(
                    source="hn", url=url, title=title, snippet=snippet,
                    detected_company="", detected_domain=extract_domain(url)
                )
            time.sleep(0.5)

        # A couple of generic security feeds (free)
        feeds = [
            "https://security.googleblog.com/feeds/posts/default?alt=rss",
            "https://feeds.feedburner.com/TheHackersNews",
        ]
        for f in feeds:
            for url, title, snippet in self._rss_pull(f):
                # print(f'RSS: {url, title,snippet}\n')
                text = f"{title} {snippet}".lower()
                if any(k in text for k in AUTH_KEYWORDS):
                    # print(f'RSS: {url, title,snippet}\n')
                    self.storage.upsert_signal(
                        source="rss", url=url, title=title, snippet=snippet,
                        detected_company="", detected_domain=extract_domain(url)
                    )
