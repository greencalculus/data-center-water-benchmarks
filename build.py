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
RETRIEVED_AI = "2026-10-12"
VERSION = "2026.10.22"
L_PER_GAL = 3.785411784

FIELDS = ["id", "publisher", "metric", "scope", "facility_or_region", "country", "period",
          "wue_l_per_kwh", "withdrawal_million_gal", "discharge_million_gal", "consumption_million_gal",
          "consumption_million_litres", "source_title", "source_url", "source_date", "retrieved", "notes",
          "energy_wh_per_prompt", "water_ml_per_prompt", "water_million_litres", "water_scope"]

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

    # ── v2026.10.12: AI per-prompt and training water (read at source 2026-10-12) ──
    g = "https://arxiv.org/abs/2508.15734"
    gt = "Elsworth et al. (Google), Measuring the environmental impact of delivering AI at Google Scale, arXiv:2508.15734 (21 Aug 2025)"
    li = "https://arxiv.org/abs/2304.03271"
    lt = "Li, Yang, Islam and Ren, Making AI Less Thirsty, arXiv:2304.03271 v5 (26 Mar 2025), Table 1"
    ai = dict(retrieved=RETRIEVED_AI)
    add(publisher="Google", metric="wue", scope="fleet", facility_or_region="Global (as used for Gemini per-prompt water)", country="",
        period="2023 and 2024", wue_l_per_kwh="1.15", source_title=gt, source_url=g, source_date="2025-08-21",
        notes="'Google's WUE Category 2 value was 1.15 L/kWh' for 2023 and 2024; water consumption (evaporated, unavailable for reuse), not withdrawal.", **ai)
    add(publisher="Google", metric="per_prompt", scope="median_prompt", facility_or_region="Gemini Apps, median text prompt (comprehensive approach)", country="",
        period="May 2025", energy_wh_per_prompt="0.24", water_ml_per_prompt="0.26", water_scope="on-site cooling (consumption)",
        source_title=gt + ", Table 2", source_url=g, source_date="2025-08-21",
        notes="Boundary: active accelerators, host CPU and DRAM, idle provisioned machines, data center overhead. Excludes networking, end-user devices and training. Water = (energy minus overhead) x WUE; electricity-generation water not included. 0.03 gCO2e.", **ai)
    add(publisher="Google", metric="per_prompt", scope="median_prompt", facility_or_region="Gemini Apps, median text prompt (existing, narrow approach)", country="",
        period="May 2025", energy_wh_per_prompt="0.10", water_ml_per_prompt="0.12", water_scope="on-site cooling (consumption)",
        source_title=gt + ", Table 2", source_url=g, source_date="2025-08-21",
        notes="Active accelerator energy only. Table 2 gives 0.12 mL; the paper's text gives 0.15 mL for the same approach. The table value is used here.", **ai)
    add(publisher="OpenAI", metric="per_prompt", scope="average_prompt", facility_or_region="ChatGPT, average query", country="",
        period="2025", energy_wh_per_prompt="0.34", water_ml_per_prompt="0.32", water_scope="not stated",
        source_title="Sam Altman, The Gentle Singularity (blog, 10 Jun 2025)", source_url="https://blog.samaltman.com/the-gentle-singularity", source_date="2025-06-10",
        notes="'about 0.000085 gallons of water; roughly one fifteenth of a teaspoon' (= 0.32 mL); 'about 0.34 watt-hours'. No method, boundary or model published.", **ai)
    add(publisher="Mistral AI", metric="per_prompt", scope="typical_response", facility_or_region="Le Chat, 400-token response (Mistral Large 2)", country="",
        period="to Jan 2025", water_ml_per_prompt="45", water_scope="life cycle (includes server manufacturing; excludes user devices)",
        source_title="Mistral AI, Our contribution to a global environmental standard for AI (22 Jul 2025)", source_url="https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai", source_date="2025-07-22",
        notes="Marginal impact per response: 1.14 gCO2e, 45 mL water, 0.16 mg Sb eq. Study with Carbone 4 and ADEME, peer-reviewed by Resilio and Hubblo. Energy per response not published.", **ai)
    add(publisher="Li et al. (UC Riverside, UT Arlington)", metric="per_prompt", scope="estimate", facility_or_region="GPT-3, medium-length response, Microsoft US average", country="US",
        period="2023 assumptions", energy_wh_per_prompt="4", water_ml_per_prompt="16.904", water_scope="on-site cooling + electricity generation",
        source_title=lt, source_url=li, source_date="2025-03-26",
        notes="Assumed 4 Wh server energy per request; PUE 1.170, on-site WUE 0.550 L/kWh, electricity water 3.142 L/kWh: 2.200 mL on site + 14.704 mL off site; 29.6 requests per 500 mL. Locations in Table 1 range 7.107 (Ireland) to 47.506 mL (Washington), the source of the '10-50 responses per 500 mL bottle' figure.", **ai)
    add(publisher="Li et al. (UC Riverside, UT Arlington)", metric="training", scope="estimate", facility_or_region="GPT-3 training, Microsoft US average", country="US",
        period="2023 assumptions", water_million_litres="5.439", water_scope="on-site cooling + electricity generation",
        source_title=lt, source_url=li, source_date="2025-03-26",
        notes="0.708 million L on site + 4.731 million L off site. The actual training location is not public.", **ai)
    add(publisher="Mistral AI", metric="training", scope="model_lifetime", facility_or_region="Mistral Large 2, training plus 18 months of use", country="",
        period="to Jan 2025", water_million_litres="281", water_scope="life cycle (includes server manufacturing; excludes user devices)",
        source_title="Mistral AI, Our contribution to a global environmental standard for AI (22 Jul 2025)", source_url="https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai", source_date="2025-07-22",
        notes="281,000 cubic metres of water; 20.4 ktCO2e; 660 kg Sb eq. Training and inference are reported together.", **ai)

    # ── v2026.10.12.1: Meta (read at source 2026-10-12; replaces the earlier "no Meta row" note, which was wrong) ──
    mu = "https://sustainability.atmeta.com/asset/2025-environmental-data-index"
    mt = "Meta 2025 Environmental Data Index, section 3 (Water)"
    for yr, v in [("2024", "0.19"), ("2023", "0.18"), ("2022", "0.20"), ("2021", "0.26"), ("2020", "0.30")]:
        add(publisher="Meta", metric="wue", scope="fleet", facility_or_region="Owned data centers (annual)", country="", period=yr,
            wue_l_per_kwh=v, source_title=mt + ", table 'Water Usage Effectiveness (WUE)'", source_url=mu, source_date="2025",
            notes="Meta: 'Annual WUE is calculated by dividing our water withdrawal, in liters, by IT electricity load, in kWh.'", **ai)
    add(publisher="Meta", metric="site_volume", scope="fleet", facility_or_region="All data centers", country="", period="2024",
        consumption_million_litres="2974", source_title=mt + ", tables 3.1 'Water Withdrawal by Facility' and 3.2 'Water Consumption'",
        source_url=mu, source_date="2025",
        notes="Published in megalitres (= million litres), so the US-gallon columns are left empty. Data centers total 2024: withdrawal 4,145 ML, consumption 2,974 ML (company total 5,637 and 3,123). Excludes 1,019 ML withdrawn for data center construction.", **ai)

    # ── v2026.10.22: Microsoft per query (read at source 2026-10-22) ──
    add(publisher="Microsoft", metric="per_prompt", scope="estimate", facility_or_region="Typical query, frontier-scale models (modelled by Microsoft researchers; not Copilot-specific)", country="",
        period="2026", energy_wh_per_prompt="0.31", water_ml_per_prompt="0.067", water_scope="on-site (data center)",
        source_title="Microsoft Cloud blog, Scaling AI with 8 to 20x energy efficiency (15 Jun 2026); Oviedo et al., Joule (Apr 2026), doi:10.1016/j.joule.2026.102430",
        source_url="https://www.microsoft.com/en-us/microsoft-cloud/blog/2026/06/15/scaling-ai-with-8-to-20x-energy-efficiency/", source_date="2026-06-15",
        notes="'a typical query uses in the range of 0.0 to 0.067 mL of water'; the upper end is given here. Energy: modelled median 0.31 Wh (interquartile range 0.16 to 0.60 Wh) from the Joule paper; long reasoning responses use more than 10x as much. Added in v2026.10.22.", retrieved="2026-10-22")

    for n, r in enumerate(out, 1):
        r["id"] = f"water-{n:04d}"
        r.setdefault("retrieved", RETRIEVED)
    return out


def main():
    data = rows()
    with open(HERE / "data-center-water.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in data:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    (HERE / "data-center-water.json").write_text(json.dumps({"version": VERSION, "retrieved": RETRIEVED_AI, "rows": data}, indent=1, ensure_ascii=False))
    print(f"{len(data)} rows")


if __name__ == "__main__":
    main()
