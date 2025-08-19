import re
from typing import List

class VisualPersonalizationAgent:
    """Create a very simple one-pager (plain text) as a visual asset placeholder."""
    def make_onepager(self, company: str, pain: str, tech: List[str]) -> str:
        fname = f"onepager_{re.sub(r'[^a-zA-Z0-9]+','_', company)[:32].lower()}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(
                "Descope – Personalized Proposal\n" +
                f"Company: {company}\n" +
                f"Observed Pain: {pain}\n" +
                f"Stack Hints: {', '.join(tech) if tech else 'N/A'}\n\n" +
                "Why Descope:\n- Faster auth integration (flows, passkeys, SAML/OIDC)\n- Reduced auth maintenance\n- Better UX & security posture\n\nNext Step: 15-min call to confirm fit and show a tailored flow.\n"
            )
        return fname
