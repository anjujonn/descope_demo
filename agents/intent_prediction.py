from typing import Dict, Any, Tuple
import datetime as dt


class IntentPredictionAgent:
    def predict(self, enriched_row: Dict[str, Any]) -> Tuple[int, str]:
        recency_bonus = 0
        # if created within last 14 days
        try:
            created = dt.datetime.fromisoformat(enriched_row.get("created_at"))
            if (dt.datetime.now(dt.timezone.utc) - created).days <= 14:
                recency_bonus = 10
        except Exception:
            pass
        roles = (enriched_row.get("hiring_roles") or "").lower()
        hiring_bonus = 8 if any(r in roles for r in ["security", "identity"]) else 0
        return recency_bonus + hiring_bonus, "recent+relevant hiring"
