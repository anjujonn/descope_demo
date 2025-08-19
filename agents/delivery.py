from typing import Any, Dict
from config import SAFE_MODE, SLACK_WEBHOOK
from storage import Storage
import requests

class DeliveryAgent:
    def __init__(self, storage: Storage, slack_webhook: str = SLACK_WEBHOOK):
        self.storage = storage
        self.webhook = None if SAFE_MODE else slack_webhook

    def notify_slack(self, lead: Dict[str, Any]):
        text = (
            f"*New High-Fit Lead*\n"
            f"Score: {lead.get('score')} | Domain: {lead.get('detected_domain')}\n"
            f"Title: {lead.get('title')}\n"
            f"URL: {lead.get('url')}\n"
        )
        payload = {"text": text}
        if not self.webhook:
            print("[SLACK MOCK]\n" + text)
            return
        try:
            r = requests.post(self.webhook, json=payload, timeout=10)
            if r.status_code >= 300:
                print("Slack webhook failed:", r.text)
        except Exception as e:
            print("Slack webhook error:", e)

    def run(self, min_score: int = 20, top_n: int = 5):
        leads = self.storage.fetch_joined(min_score=min_score)[:top_n]
        for ld in leads:
            self.notify_slack(ld)
