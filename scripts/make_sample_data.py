"""
Generate the synthetic demo dataset used by the public dashboard.

Every founder, startup, and website in data/startups.json and dashboard/data.js
is made up by this script. Names are random first/last-name pairings, startup
names are random word combinations, websites use the reserved .example TLD,
and LinkedIn URLs are left empty. The output mirrors the real pipeline's
schema and rough mix of sectors, tiers, and sources, so the dashboard behaves
the same way it does on live data.

Usage:
    python make_sample_data.py            # writes 240 records
    python make_sample_data.py --n 500
"""

import argparse
import json
import random
from pathlib import Path

SEED = 42

FIRST = [
    "Aarav", "Diya", "Kabir", "Meera", "Rohan", "Ananya", "Vikram", "Isha",
    "Arjun", "Nisha", "Karan", "Pooja", "Siddharth", "Tara", "Aditya", "Riya",
    "Varun", "Sneha", "Nikhil", "Kavya", "Rahul", "Aisha", "Dev", "Priya",
    "Harsh", "Lakshmi", "Manav", "Zoya", "Neel", "Sana",
]
LAST = [
    "Sharma", "Iyer", "Mehta", "Reddy", "Nair", "Kapoor", "Gupta", "Rao",
    "Bose", "Menon", "Joshi", "Pillai", "Verma", "Kulkarni", "Desai", "Banerjee",
    "Chatterjee", "Saxena", "Malhotra", "Shetty", "Agarwal", "Krishnan",
]

PREFIX = [
    "Nimbus", "Kosha", "Vela", "Tarang", "Orbit", "Pulse", "Saffron", "Lumen",
    "Ember", "Arka", "Prana", "Zephyr", "Indigo", "Koru", "Neev", "Sutra",
    "Halo", "Bindu", "Quill", "Mitra", "Vayu", "Chakra", "Nova", "Ankur",
]
SUFFIX = {
    "Consumer AI": ["AI", "Labs", "Mind", "Wise", "Stack"],
    "Consumer Tech": ["Kart", "Bay", "Hub", "Loop", "ly", "Works"],
    "HealthTech": ["Health", "Care", "Fit", "Med", "Well"],
}

ONE_LINERS = {
    "Consumer AI": [
        "AI tutor that explains school maths in regional languages",
        "Voice-first assistant for small shop owners to track sales",
        "Generative AI tool that turns product photos into catalogue listings",
        "AI travel planner that builds budget itineraries for Indian cities",
        "Personal finance copilot that categorises UPI spending",
        "AI interview coach for first-time job seekers",
        "Vernacular chatbot that answers government scheme questions",
        "AI resume builder tuned for Indian campus placements",
    ],
    "Consumer Tech": [
        "Subscription marketplace for home-cooked tiffin meals",
        "Social commerce app for regional fashion sellers",
        "Micro-savings app that rounds up daily UPI payments",
        "Peer-to-peer rental platform for party and event gear",
        "Creator storefront for selling digital courses in Hindi",
        "Hyperlocal delivery app for neighbourhood grocery stores",
        "Gamified quiz app for competitive exam preparation",
        "D2C brand for sustainable everyday kitchenware",
    ],
    "HealthTech": [
        "Remote physiotherapy programmes delivered over video",
        "Women's health app for cycle tracking and teleconsults",
        "Elder-care platform connecting families with trained caregivers",
        "Mental wellness app offering guided therapy in regional languages",
        "Diagnostics booking platform with home sample collection",
        "Nutrition coaching app for managing lifestyle conditions",
        "Clinic management software for single-doctor practices",
        "Dental aligner brand with tele-orthodontist follow-ups",
    ],
}

SECTOR_WEIGHTS = {"Consumer AI": 45, "Consumer Tech": 40, "HealthTech": 15}

TIER_RATIONALES = {
    1: ["IIT Bombay alumni", "IIT Delhi alumni", "BITS Pilani alumni", "IIM Ahmedabad alumni",
        "Ex-Swiggy", "Ex-Razorpay", "Ex-CRED", "Ex-Flipkart", "Ex-Google",
        "Strong traction (revenue)", "Strong traction (million users)"],
    2: ["Some funding/accelerator signals"],
    3: ["Early stage, limited public info"],
}
TIER_WEIGHTS = {1: 35, 2: 30, 3: 35}

SOURCES = [
    "Enricher", "hn:show_hn:ai", "hn:show_hn:saas", "hn:show_hn:d2c",
    "news:news:angel", "news:news:stealth_exit", "reddit:r/developersIndia",
    "directory:startup_india", "browser:Accelerator portfolio", "Web Search",
]


def make_records(n: int) -> list[dict]:
    rng = random.Random(SEED)
    seen = set()
    records = []
    while len(records) < n:
        sector = rng.choices(list(SECTOR_WEIGHTS), weights=SECTOR_WEIGHTS.values())[0]
        startup = f"{rng.choice(PREFIX)}{rng.choice(SUFFIX[sector])}"
        if startup in seen:
            continue
        seen.add(startup)
        tier = rng.choices(list(TIER_WEIGHTS), weights=TIER_WEIGHTS.values())[0]
        records.append({
            "founder_name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "startup_name": startup,
            "linkedin_url": None,
            "website": f"https://{startup.lower()}.example",
            "sector": sector,
            "one_liner": rng.choice(ONE_LINERS[sector]),
            "tier": tier,
            "tier_rationale": rng.choice(TIER_RATIONALES[tier]),
            "source": rng.choice(SOURCES),
            "founded_year": rng.choices([2022, 2023, 2024, 2025], weights=[5, 15, 55, 25])[0],
            "funding_stage": rng.choice(["Seeking Pre-Seed", "Pre-Seed", "Bootstrapped", None]),
            "city": rng.choice(["Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad", "Pune", "Chennai", None]),
            "is_new": rng.random() < 0.15,
        })
    records.sort(key=lambda r: (r["tier"], r["startup_name"]))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--n", type=int, default=240, help="number of records")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    records = make_records(args.n)
    (root / "data" / "startups.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "dashboard" / "data.js").write_text(
        "// SYNTHETIC DEMO DATA. Generated by scripts/make_sample_data.py. All names are fictional.\n"
        "const STARTUPS_DATA = " + json.dumps(records, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    print(f"Wrote {len(records)} synthetic records")


if __name__ == "__main__":
    main()
