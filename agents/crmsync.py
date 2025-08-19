from typing import List, Any, Dict
import json

class CRMSyncAgent:
    def export_json(self, leads: List[Dict[str, Any]], path: str = "crm_export.json") -> str:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2)
        return path