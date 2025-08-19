import json
from config import AUTH_KEYWORDS
from storage import Storage


class ScoringAgent:
    """NOTE: Scoring is very basic and uses extremely simple rules"""
    def __init__(self, storage: Storage):
        self.storage = storage

    def run(self):
        joined = self.storage.fetch_joined(min_score=0)  # pull all
        print(f"joined: {joined}")
        for row in joined:
            text = f"{row.get('title','')}\n{row.get('snippet','')}".lower()
            score = 0
            reasons = []
            # keyword strength
            for kw in AUTH_KEYWORDS:
                if kw in text:
                    score += 3
            # tech hints weight
            tech = json.loads(row.get("tech_hints") or "{}")
            if tech.get("Descope"): score += 5; reasons.append("mentions Descope")
            if tech.get("Auth0"): score += 8; reasons.append("Auth0 present")
            if tech.get("Okta"): score += 8; reasons.append("Okta present")
            if tech.get("FirebaseAuth"): score += 5; reasons.append("Firebase Auth present")
            if tech.get("SAML"): score += 4; reasons.append("SAML in stack")
            if tech.get("OIDC"): score += 4; reasons.append("OIDC in stack")
            # size hint
            size = (row.get("company_size_hint") or "unknown")
            size_weight = {"51-250": 6, "251-1000": 10, ">1000": 12}
            score += size_weight.get(size, 2)
            reasons.append(f"size={size}")
            # hiring roles
            roles = (row.get("hiring_roles") or "").split(",") if row.get("hiring_roles") else []
            for r in roles:
                if r.strip() in {"security","identity","backend","platform","devops"}:
                    score += 2
            if roles:
                reasons.append(f"hiring={','.join([r.strip() for r in roles if r.strip()])}")
            # cap and write
            score = min(score, 100)
            self.storage.upsert_score(signal_url=row["url"], score=score, reasons=reasons)
