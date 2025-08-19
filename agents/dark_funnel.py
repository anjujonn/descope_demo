from typing import List, Any, Dict
import os, re
class DarkFunnelAgent:
    def parse_csv(self, path: str) -> List[str]:
        if not os.path.exists(path):
            return []
        out = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "," in line:
                    parts = [p.strip() for p in line.split(",")]
                    if parts and re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", parts[-1]):
                        out.append(parts[-1].lower())
        return sorted(set(out))
