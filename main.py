
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from agents import (
    CompetitiveSwitcherDetector,
    CRMSyncAgent,
    DeliveryAgent,
    EnrichmentAgent,
    HyperPersonalizationAgent,
    IntentPredictionAgent,
    MessagingAgent,
    MultiThreadingAgent,
    ScoringAgent,
    SignalDetectionAgent,
    VisualPersonalizationAgent,
    CreativeOutreachAgent
)
from config import DB_PATH
from storage import Storage


def bootstrap_demo_data(storage: Storage):
    sd = SignalDetectionAgent(storage)
    sd.run()
    en = EnrichmentAgent(storage)
    en.run()
    sc = ScoringAgent(storage)
    sc.run()


def run_demo(storage: Storage, use_llm: bool = False):
    msg = MessagingAgent(storage)
    msg.run(min_score=10, use_llm=use_llm)
    dv = DeliveryAgent(storage)
    dv.run(min_score=20, top_n=3)

    # additional layers
    leads = storage.fetch_joined(min_score=10)
    ip = IntentPredictionAgent()
    csw = CompetitiveSwitcherDetector()
    mt = MultiThreadingAgent()
    hyp = HyperPersonalizationAgent()
    vis = VisualPersonalizationAgent()
    crm = CRMSyncAgent()


    enriched_export = []
    for ld in leads[:5]:
        bonus, why = ip.predict(ld)
        diss = csw.detect((ld.get("title") or "") + "\n" + (ld.get("snippet") or ""))
        personas = mt.suggest_personas(ld.get("company_size_hint") or "unknown", ld.get("hiring_roles") or "")
        hook = hyp.recent_hook(ld.get("detected_domain") or "")
        onepager = vis.make_onepager(ld.get("detected_domain") or "company", ld.get("title") or "auth friction", list(json.loads(ld.get("tech_hints") or "{}").keys()))

        agent = CreativeOutreachAgent(storage, "./Descope")
        results = agent.run_for_top_leads(top_n=5)

        enriched_export.append({
            "url": ld.get("url"),
            "domain": ld.get("detected_domain"),
            "base_score": ld.get("score"),
            "intent_bonus": bonus,
            "switcher_risk": diss,
            "personas": personas,
            "hook": hook,
            "onepager_path": onepager,
            "creative_outreach": results,
        })

    path = crm.export_json(enriched_export)
    print(f"CRM export written to: {path}")

def main():
    parser = argparse.ArgumentParser(description="Descope AI GTM – free 14-agent prototype")
    parser.add_argument("--bootstrap", action="store_true", help="Collect signals, enrich, score")
    parser.add_argument("--run-demo", action="store_true", help="Generate messages & deliver Slack alerts")
    parser.add_argument("--use-ollama", action="store_true", help="Use local LLM via Ollama for refining copy")
    args = parser.parse_args()

    storage = Storage(DB_PATH)

    if args.bootstrap:
        print("[BOOTSTRAP] Collecting signals → enriching → scoring...")
        bootstrap_demo_data(storage)
        print("[BOOTSTRAP] Done.")

    if args.run_demo:
        print("[RUN] Messaging, delivery, and advanced layers...")
        run_demo(storage, use_llm=args.use_ollama)
        print("[RUN] Done.")

    if not (args.bootstrap or args.run_demo):
        parser.print_help()

if __name__ == "__main__":
    main()
