import json
from typing import List

import requests
from config import OLLAMA_MODEL, SAFE_MODE
from storage import Storage


class MessagingAgent:
    def __init__(self, storage: Storage):
        self.storage = storage

    def _template_email(self, company: str, pain: str, tech: List[str]) -> str:
        tech_str = ", ".join(tech) if tech else "modern auth"
        return (
            f"Subject: Quick idea to de-risk {company}'s auth\n\n"
            f"Hi team,\n\n"
            f"I came across a recent discussion indicating challenges around \"{pain}\".\n"
            f"If you're currently using {tech_str}, you might like Descope's low-code auth flows (passkeys, SAML/OIDC, social),\n"
            f"which can reduce integration time and improve security posture.\n\n"
            f"Happy to share a quick flow mock for your stack. Would early next week be a bad time?\n\n"
            f"– Ananya\n"
        )

    def _ollama_refine(self, text: str) -> str:
        try:
            resp = requests.post("http://localhost:11434/api/generate", json={
                "model": None if SAFE_MODE else OLLAMA_MODEL,
                "prompt": (
                    "Rewrite the following cold email to be concise (80-120 words),\n"
                    "personal yet professional, with a clear CTA for a 15-min chat.\n\n" + text
                )
            }, timeout=30)
            if resp.status_code == 200:
                out = resp.json().get("response", "").strip()
                return out or text
        except Exception:
            pass
        return text

    def run(self, min_score: int = 10, use_llm: bool = False):
        leads = self.storage.fetch_joined(min_score=min_score)
        for ld in leads:
            company = (ld.get("detected_company") or ld.get("detected_domain") or "your team")
            pain = ld.get("title") or "auth/SSO friction"
            tech = list(json.loads(ld.get("tech_hints") or "{}").keys())
            msg = self._template_email(company, pain, tech)
            if use_llm:
                msg = self._ollama_refine(msg)
            self.storage.insert_outreach(signal_url=ld["url"], channel="email", message=msg, status="draft")
