#!/usr/bin/env python3
"""Build data-center-water.csv / .json from the source snapshot and hand-checked rows.

Two kinds of row, distinguished by `metric`:
  - wue: litres of site water per kWh of IT energy (The Green Grid / ISO/IEC 30134-9),
    as each operator or body publishes it.
  - site_volume: a site's yearly water withdrawal, discharge and consumption in
    million US gallons (Google publishes these per location).
Values are copied exactly as published; nothing is estimated or converted except
the litre column on site_volume rows (US gallons × 3.785411784).

    python3 build.py
"""
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).parent
RETRIEVED = "2026-10-11"
L_PER_GAL = 3.785411784

FIELDS = ["id", "publisher", "metric", "scope", "facility_or_region", "country", "period",
          "wue_l_per_kwh", "withdrawal_million_gal", "discharge_million_gal", "consumption_million_gal",
          "consumption_million_litres", "source_title", "source_url", "source_date", "retrieved", "notes"]

GOOGLE_URL = "https://sustainability.google/files/google-2026-environmental-report.pdf"
GOOGLE_TITLE = "Google 2026 Environmental Report (FY2025), table 'Water use by data center location'"
AWS_URL = "https://sustainability.aboutamazon.com/products-services/aws-cloud"
AWS_TITLE = "Amazon Sustainability: AWS Cloud (AWS Region PUE and WUE table)"

US_STATES = {"VA", "SC", "IA", "OR", "GA", "NV", "AL", "OH", "NC", "OK", "AZ", "TX", "TN", "IN", "NE"}
COUNTRY = {"Ireland": "IE", "Netherlands": "NL", "Germany": "DE", "Denmark": "DK", "Finland": "FI",
           "Japan": "JP", "Canada": "CA", "Chile": "CL", "Belgium": "BE", "Australia": "AU"}
AWS_COUNTRY = {
    "Frankfurt": "DE", "Ireland": "IE", "London": "GB", "Paris": "FR", "Spain": "ES", "Stockholm": "SE",
    "Bahrain": "BH", "Tel Aviv": "IL", "UAE": "AE", "Cape Town": "ZA", "Bangkok": "TH", "Hyderabad": "IN",
    "Jakarta": "ID", "Melbourne": "AU", "Mumbai": "IN", "Osaka": "JP", "Singapore": "SG", "Sydney": "AU",
    "Tokyo": "JP", "Ningxia": "CN", "Sao Paulo": "BR", "Northern Virginia": "US", "Ohio": "US",
    "Northern California": "US", "Oregon": "US", "Central": "CA", "West": "CA",
}


def num(s):
    return float(str(s).replace(",", ""))


def country_of(site):
    tail = site.split(",")[-1].strip()
    if tail in US_STATES:
        return "US"
    return COUNTRY.get(tail, "")


def rows():
    snap = json.loads((HERE / "sources_snapshot.json").read_text())
    out = []

    for name, wd, dc, cons in snap["google_sites_2025"]:
        total = name == "Data centers total"
        out.append({
            "publisher": "Google", "metric": "site_volume",
            "scope": "fleet" if total else ("other_sites" if name.startswith("Other") else "site"),
            "facility_or_region": "All data centers" if total else name,
            "country": "" if total or name.startswith("Other") else country_of(name),
            "period": "2025", "withdrawal_million_gal": wd.replace(",", ""), "discharge_million_gal": dc.replace(",", ""),
            "consumption_million_gal": cons.replace(",", ""),
            "consumption_million_litres": round(num(cons) * L_PER_GAL, 1),
            "source_title": GOOGLE_TITLE, "source_url": GOOGLE_URL, "source_date": "2026",
            "notes": "Consumption = withdrawal minus discharge (Google's definition). 2025 metrics subject to third-party limited assurance per the report.",
        })

    head = snap["aws_regions"][0]
    i25 = head.index("WUE 2025")
    for r in snap["aws_regions"][1:]:
        v = r[i25]
        if v in ("--", "---", ""):
            continue
        inner = r[0][r[0].find("(") + 1:r[0].rfind(")")]
        out.append({
            "publisher": "Amazon Web Services", "metric": "wue", "scope": "cloud_region", "facility_or_region": r[0],
            "country": AWS_COUNTRY.get(inner, ""), "period": "2025", "wue_l_per_kwh": v,
            "source_title": AWS_TITLE, "source_url": AWS_URL, "source_date": "2025 column",
            "notes": "AWS WUE = water withdrawn per kWh of IT load; regions with under 12 months of operation show no value.",
        })

    def add(**kw):
        kw.setdefault("notes", "")
        out.append(kw)

    add(publisher="Amazon Web Services", metric="wue", scope="fleet", facility_or_region="Global", country="", period="2025",
        wue_l_per_kwh="0.12", source_title="AWS Sustainability", source_url="https://aws.amazon.com/sustainability/", source_date="2026",
        notes="'a global data center WUE of 0.12 liters of water withdrawn per kilowatt-hour of IT Load (L/kWh) in 2025, a 20% improvement from 2024'")
    ms = "https://datacenters.microsoft.com/sustainability/efficiency/"
    for region, fy24, fy25 in [("Global", "0.30", "0.27"), ("Americas", "0.38", "0.34"),
                               ("Asia Pacific", "0.03", "0.25"), ("Europe, Middle East & Africa", "0.03", "0.03")]:
        for fy, v, per in [("FY25", fy25, "Jul 2024 to Jun 2025"), ("FY24", fy24, "Jul 2023 to Jun 2024")]:
            add(publisher="Microsoft", metric="wue", scope="fleet" if region == "Global" else "geographic_region",
                facility_or_region=region, country="", period=f"{fy} ({per})", wue_l_per_kwh=v,
                source_title="Microsoft Datacenters: Efficiency (PUE and WUE by region)", source_url=ms, source_date=fy,
                notes="WUE = annual litres used for humidification and cooling / annual IT kWh; owned and controlled datacenters operating 12 months." +
                      (" Asia Pacific moved from 0.03 to 0.25; Microsoft does not explain the change." if region == "Asia Pacific" and fy == "FY25" else ""))
    add(publisher="Equinix", metric="wue", scope="fleet", facility_or_region="Global portfolio", country="", period="2025",
        wue_l_per_kwh="0.91", source_title="Equinix FY2025 Annual Report (SEC Form ARS)",
        source_url="https://www.sec.gov/Archives/edgar/data/1101239/000110123926000075/EQIXAnnualRpt2025PRINT.pdf", source_date="2026",
        notes="'0.91 average water usage effectiveness of our entire global portfolio of data centers'")
    add(publisher="Digital Realty", metric="wue", scope="fleet", facility_or_region="Global portfolio", country="", period="2025",
        wue_l_per_kwh="0.59", source_title="Digital Realty press release: 2025 Impact Report (27 May 2026)",
        source_url="https://mfn.se/all/a/digital-realty/digital-realty-publishes-2025-impact-report-highlighting-sustainability-progress-f0a795c9",
        source_date="2026-05-27", notes="'Water usage effectiveness (WUE) of 0.59 across the global portfolio, a 15.7% improvement from the prior year'")
    ec = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52026DC0500"
    add(publisher="European Commission", metric="wue", scope="regulatory_average", facility_or_region="EU reporting data centres that use water (energy-weighted average)",
        country="", period="2024", wue_l_per_kwh="0.58",
        source_title="European Commission, COM(2026) 500 final, section 2.2.2 (21 Sep 2026)", source_url=ec, source_date="2026-09-21",
        notes="458 data centres with reliable WUE; sites reporting zero water (dry cooling) excluded; Member State averages 0.07 to 1.28. Climate Neutral Data Centre Pact target: 0.4 by 2040.")

    for n, r in enumerate(out, 1):
        r["id"] = f"water-{n:04d}"
        r["retrieved"] = RETRIEVED
    return out


def main():
    data = rows()
    with open(HERE / "data-center-water.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in data:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    (HERE / "data-center-water.json").write_text(json.dumps({"retrieved": RETRIEVED, "rows": data}, indent=1, ensure_ascii=False))
    print(f"{len(data)} rows")


if __name__ == "__main__":
    main()
