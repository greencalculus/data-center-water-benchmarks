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
VERSION = "2026.10.22.2"
L_PER_GAL = 3.785411784

FIELDS = ["id", "publisher", "metric", "scope", "facility_or_region", "country", "period",
          "wue_l_per_kwh", "withdrawal_million_gal", "discharge_million_gal", "consumption_million_gal",
          "consumption_million_litres", "source_title", "source_url", "source_date", "retrieved", "notes",
          "energy_wh_per_prompt", "water_ml_per_prompt", "water_million_litres", "water_scope",
          "value", "unit", "figure_type"]

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

    # ── v2026.10.22.2: AI and hyperscale campuses + US totals (read at source 2026-10-22) ──
    # figure_type says what kind of number each is: bills, projection, permit, statement or model.
    c = dict(metric="campus_water", scope="site", country="US", retrieved="2026-10-22")
    dm = ("Daily Memphian (Hardiman), Analyzing xAI's MLGW bills (29 Dec 2025, updated 12 Jan 2026)", "https://dailymemphian.com/article/58474/analyzing-xai-mlgw-bills", "2025-12-29")
    mf = ("Memphis Flyer, Protect Our Aquifer: xAI Bought 25M Gallons of Water from MLGW, Projects Increases (22 May 2026)", "https://www.memphisflyer.com/protect-our-aquifer-xai-bought-25m-gallons-of-water-from-mlgw-projects-increases/", "2026-05-22")
    gv = ("Governing (Smith), Wastewater Will Cool This Memphis Data Center (16 Mar 2026)", "https://www.governing.com/resilience/wastewater-will-cool-this-memphis-data-center", "2026-03-16")
    adv = ("The Advocate (Abugov), Meta Louisiana data center water (21 Dec 2025)", "https://www.theadvocate.com/baton_rouge/news/environment/meta-louisiana-data-center-water-ai/article_02443429-0857-5574-a194-64839996bc52.html", "2025-12-21")
    kj1 = ("KJZZ (Reznick), Project Blue would have used millions of gallons of Tucson water. Residents, city leaders said no. (11 Aug 2025)", "https://www.kjzz.org/fronteras-desk/2025-08-11/project-blue-would-have-used-millions-of-gallons-of-tucson-water-residents-city-leaders-said-no", "2025-08-11")
    kj2 = ("KJZZ / AZPM (Mendoza), Project Blue data center could use up to 31 million gallons of water per year (29 May 2026)", "https://www.kjzz.org/fronteras-desk/2026-05-29/project-blue-data-center-could-use-up-to-31-million-gallons-of-water-per-year", "2026-05-29")
    orc = ("Oracle Fact Sheet: Stargate Data Centers (23 Sep 2025)", "https://arrington.house.gov/UploadedFiles/FINAL_Oracle_OAI_Data_Center_Fact_Sheet_092225b.pdf", "2025-09-23")
    tt = ("Texas Tribune (Martinez, Lozano Carver), Texas data center water use (25 Sep 2025)", "https://www.texastribune.org/2025/09/25/texas-data-center-water-use/", "2025-09-25")
    msl = ("Microsoft Local, Understanding water use at Microsoft datacenters", "https://local.microsoft.com/blog/understanding-water-use-at-microsoft-datacenters/", "2026")
    msb = ("Microsoft (Guthrie), Inside the world's most powerful AI datacenter (18 Sep 2025)", "https://blogs.microsoft.com/blog/2025/09/18/inside-the-worlds-most-powerful-ai-datacenter/", "2025-09-18")
    def cw(src, **kw):
        t, u, d = src
        add(source_title=t, source_url=u, source_date=d, **{**c, **kw})
    cw(dm, publisher="xAI (MLGW bills, via Daily Memphian)", facility_or_region="Colossus, Memphis, TN", period="2025-08-03/2025-09-04",
       value="381000", unit="US gallons per day (peak)", figure_type="utility_bills",
       notes="'Colossus had a peak water usage of about 381,000 gallons a day from Aug. 3 to Sept. 4, 2025', from copies of xAI's MLGW bills; projections had been more than 1 million gallons a day.")
    cw(mf, publisher="xAI (Protect Our Aquifer, via Memphis Flyer)", facility_or_region="Colossus, Memphis, TN", period="2026-03",
       value="25", unit="million US gallons per month (more than)", figure_type="advocacy_group_report",
       notes="'purchased more than 25 million gallons of water from Memphis Light, Gas, and Water (MLGW) in March'; POA also gives 812,502 gallons a day pumped from the Memphis Sand Aquifer (basis not stated).")
    cw(gv, publisher="xAI", facility_or_region="Colossus, Memphis, TN (open cooling loop)", period="2026",
       value="3", unit="million US gallons per day (stated need)", figure_type="operator_statement",
       notes="xAI engineer Mark Carroll: the closed loop water 'doesn't need replacing' but 'the open loop at Colossus needs 3 million gallons a day'. Cooling towers evaporate about 85%. Water recycling plant (treated wastewater) under construction since Oct 2025; end-2026 target 'hazy'.")
    cw(adv, publisher="Meta", facility_or_region="Hyperion, Richland Parish, LA", period="2028 onward",
       value="500-600", unit="million US gallons per year (projected)", figure_type="operator_projection",
       notes="About 1.5 million gallons a day on average, from the Mississippi River Alluvial Aquifer; closed-loop cooling, no water needed for more than half the year, new water above about 90 F. Meta agreed to voluntary annual water reports for its first five years.")
    cw(adv, publisher="Meta (Louisiana state records)", facility_or_region="Hyperion, Richland Parish, LA", period="registration",
       value="23", unit="million US gallons per day (registered, more than)", figure_type="state_registration",
       notes="'registered to consume more than 23 million gallons of water per day', or 8.4 billion gallons a year, per state records and the company.")
    cw(kj1, publisher="Beale Infrastructure (Project Blue)", facility_or_region="Project Blue, Tucson, AZ (proposal)", period="full build-out",
       value="1910", unit="acre-feet per year (at least)", figure_type="development_proposal",
       notes="'at least 1,910 acre feet per year at full build out', about 6% of Tucson's total water supply; potable water for at least the first two years before reclaimed water. City council voted unanimously to end negotiations (Aug 2025). 1,910 acre-feet = about 622 million US gallons at 325,851 gallons per acre-foot (GreenCalculus conversion). 2023 public records tied the project to AWS, which said it had no current commitments.")
    cw(kj2, publisher="Beale Infrastructure (Bobcat Tucson Water LLC)", facility_or_region="Project Blue, Pima County, AZ", period="2026",
       value="31", unit="million US gallons per year (up to)", figure_type="state_regulator",
       notes="Arizona Department of Water Resources: the data center under construction in Pima County 'could use up to 31 million gallons of water per year'; two commercial wells applied for in January 2026.")
    cw(orc, publisher="Oracle / OpenAI", facility_or_region="Stargate, Abilene, TX", period="operations",
       value="12625", unit="US gallons per building per year (estimated)", figure_type="operator_estimate",
       notes="'The anticipated water usage for cooling system maintenance and quality purposes totals approximately 12,625 gallons per building per year.' Closed-loop, non-evaporative liquid cooling; eight buildings = about 101,000 gallons a year (GreenCalculus calculation).")
    cw(tt, publisher="Oracle / OpenAI (Texas Tribune)", facility_or_region="Stargate, Abilene, TX (first fill)", period="2025",
       value="8", unit="million US gallons (one-off fill)", figure_type="press_report",
       notes="'will initially use 8 million gallons of Abilene city water to fill the cooling system'; the city's average daily use is 22 million gallons. Other outlets report about 1 million gallons.")
    cw(msl, publisher="Microsoft", facility_or_region="Fairwater, Mount Pleasant, WI", period="operations",
       value="", unit="", figure_type="operator_statement",
       notes="'uses about as much water as a typical restaurant each year'; no gallon figure published. Over 90% of capacity on closed-loop liquid cooling filled once during construction; the other 10% uses outdoor air, 'switching to water only during the hottest days' (Microsoft blog, 18 Sep 2025: " + msb[1] + ").")
    lb = ("Shehabi et al., 2024 United States Data Center Energy Usage Report, LBNL (doi:10.71468/P1WC7Q), chapters 4-5", "https://escholarship.org/uc/item/32d6m0d1", "2024-12-20")
    n = dict(metric="national_estimate", scope="country", country="US", facility_or_region="All US data centers", retrieved="2026-10-22", figure_type="model_estimate")
    for per, v, unit, note in [
        ("2014", "21200", "million litres (on site)", "'In 2014, data centers consumed 21.2 billion liters of water, with 64% in internal data centers.'"),
        ("2023", "66000", "million litres (on site)", "'By 2023, hyperscale and colocation account for 84% of the 66-billion-liter total' (about 17.4 billion US gallons)."),
        ("2028", "60000-124000", "million litres (on site, hyperscale only, projected)", "'Hyperscale data centers in 2028 are expected to consume between 60 and 124 billion liters.'"),
        ("2023", "800000", "million litres (electricity generation, nearly)", "'The total indirect water footprint of U.S. data centers is nearly 800 billion liters'; 176 TWh in 2023."),
        ("2023", "4.52", "litres per kWh (electricity generation)", "'national average of 4.52 L/kWh of indirect water consumption' for data center electricity, against 4.35 L/kWh for all US electricity."),
        ("2014-2023", "0.36", "litres per kWh IT (average site WUE)", "Average WUE 'stays just over 0.36 L/kWh through 2023'."),
        ("after 2023", "0.45-0.48", "litres per kWh IT (average site WUE, projected)", "'the average WUE rises slightly, reaching between 0.45 and 0.48 L/kWh, reflecting increasing WUEs in the hyperscale and colocation data centers, along with the increased water consumption of liquid-cooled systems.'")]:
        add(publisher="Lawrence Berkeley National Laboratory", period=per, value=v, unit=unit, notes=note,
            source_title=lb[0], source_url=lb[1], source_date=lb[2], **n)
    add(publisher="Houston Advanced Research Center (via Texas Tribune)", metric="national_estimate", scope="state", country="US",
        facility_or_region="Texas, all data centers", period="2025", value="25000", unit="million US gallons per year (estimated)",
        figure_type="model_estimate", source_title=tt[0], source_url=tt[1], source_date=tt[2], retrieved="2026-10-22",
        notes="'approximately 25 billion gallons of water, or 0.4% of the state's total water use in 2025'; 'By 2030, this demand could increase up to 2.7%'.")

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
