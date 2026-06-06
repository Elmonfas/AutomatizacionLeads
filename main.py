#!/usr/bin/env python3
"""Main entry point — scrape, analyze, score, save, open dashboard."""

import asyncio
import csv
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
DATA_PATH = Path(__file__).parent / "leads_data.json"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_json(leads):
    data = []
    for l in leads:
        data.append({
            "urgency_score": l.urgency_score,
            "name": l.name,
            "address": l.address,
            "phone": l.phone,
            "email": l.email,
            "website": l.website,
            "has_website": l.has_website,
            "rating": l.rating,
            "reviews_count": l.reviews_count,
            "pagespeed_mobile": l.pagespeed_mobile,
            "pagespeed_desktop": l.pagespeed_desktop,
            "has_ssl": l.has_ssl,
            "is_mobile_friendly": l.is_mobile_friendly,
            "web_looks_old": l.web_looks_old,
            "tech_stack": l.tech_stack,
            "problem_summary": l.problem_summary,
            "whatsapp_message": l.whatsapp_message,
            "maps_url": l.maps_url,
        })
    data.sort(key=lambda x: x["urgency_score"] or 0, reverse=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def export_csv(data: list, output_file: str):
    fieldnames = list(data[0].keys()) if data else []
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            row_copy = dict(row)
            row_copy["tech_stack"] = "; ".join(row_copy.get("tech_stack") or [])
            writer.writerow(row_copy)


def print_summary(data: list, output_file: str):
    total = len(data)
    no_web = sum(1 for l in data if not l["has_website"])
    bad_web = sum(
        1 for l in data
        if l["has_website"] and l["pagespeed_mobile"] is not None and l["pagespeed_mobile"] < 50
    )
    sep = "─" * 60
    print(f"\n{sep}")
    print("  RESUMEN")
    print(sep)
    print(f"  Total encontrados : {total}")
    print(f"  Sin web           : {no_web}")
    print(f"  Web mala (<50)    : {bad_web}")
    print(f"\n  TOP 5 LEADS:")
    print(sep)
    for i, l in enumerate(data[:5], 1):
        print(f"  {i}. [{l['urgency_score']}/10] {l['name']}")
        print(f"     {l['problem_summary']}")
        print()
    print(sep)
    print(f"\n  Dashboard: http://localhost:5050")
    print(sep)


async def run_pipeline(cfg: dict):
    from scraper import scrape_google_maps
    from analyzer import analyze_all
    from scorer import score_all

    print(f"\n{'='*60}")
    print(f"  PROSPECTOR — {cfg['search_query']}")
    print(f"{'='*60}\n")

    print("[1/3] Scraping Google Maps...")
    leads = await scrape_google_maps(
        cfg["search_query"],
        cfg["max_results"],
        cfg["delays"]["min_seconds"],
        cfg["delays"]["max_seconds"],
    )
    print(f"  → {len(leads)} negocios\n")
    if not leads:
        print("[error] Sin resultados. Cambia la query en config.json.")
        sys.exit(1)

    print("[2/3] Analizando presencia digital...")
    leads = await analyze_all(leads)
    print()

    print("[3/3] Scoring heurístico...")
    leads = score_all(leads, cfg["freelancer_name"], cfg["freelancer_city"])
    print()

    data = save_json(leads)
    export_csv(data, cfg["output_file"])
    print_summary(data, cfg["output_file"])


def start_dashboard():
    from app import create_app
    flask_app = create_app()
    # Open browser after short delay
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5050")).start()
    flask_app.run(host="0.0.0.0", port=5050, debug=False)


if __name__ == "__main__":
    cfg = load_config()

    if "--dashboard" in sys.argv:
        print("Abriendo dashboard en http://localhost:5050 ...")
        start_dashboard()
    elif "--pipeline-only" in sys.argv:
        # Called from the dashboard's /api/run — just run pipeline, no Flask
        asyncio.run(run_pipeline(cfg))
    else:
        asyncio.run(run_pipeline(cfg))
        print("\nAbriendo dashboard...")
        start_dashboard()
