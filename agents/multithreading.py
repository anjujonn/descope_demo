from typing import List

class MultiThreadingAgent:
    def suggest_personas(self, size_hint: str, roles: str) -> List[str]:
        personas = ["CTO", "Head of Engineering", "Security Lead", "Platform Lead"]
        if size_hint in {"251-1000", ">1000"}:
            personas += ["IAM Architect", "Compliance Lead"]
        if "mobile" in (roles or ""):
            personas += ["Mobile Lead"]
        return sorted(set(personas))
