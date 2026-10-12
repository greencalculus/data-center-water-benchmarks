# Data Center Water Benchmarks

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23290085.svg)](https://doi.org/10.5281/zenodo.23290085)

Publicly disclosed data center and AI water figures, each traced to its publisher: water usage effectiveness (WUE) by operator and region, yearly water withdrawal, discharge and consumption by site, and water per AI prompt and per model trained.

- **85 rows** from 10 publishers: Google (water by data center location, 2025: 40 named sites, other sites and the total; fleet WUE 2023 and 2024; Gemini water per prompt, May 2025), Amazon Web Services (global and 17 cloud regions, 2025), Microsoft (global and 3 regions, FY24 and FY25), Equinix and Digital Realty (portfolio WUE, 2025), the European Commission (EU average WUE, 2024), Meta (data center WUE 2020 to 2024 and 2024 water consumption), OpenAI (ChatGPT water per query, 2025), Mistral AI (life-cycle water per Le Chat response and for Mistral Large 2) and Li et al. (GPT-3 per-response and training estimates).
- **Each value is copied exactly** as the publisher printed it. The only derived column is `consumption_million_litres` (US gallons × 3.785411784).
- **Retrieved 11 October 2026** (rows 72 to 85: 12 October 2026). Every row records its source URL and the table or document it came from.

Interactive versions with calculators: https://greencalculus.com/data/data-center-water-usage/ (data centers) and https://greencalculus.com/data/ai-water-usage/ (water per AI prompt).

## Columns

| Column | Meaning |
|---|---|
| `id` | Row id, stable within a version |
| `publisher` | Who published the figure |
| `metric` | `wue` (litres per kWh of IT energy), `site_volume` (million US gallons per year), `per_prompt` (water per AI prompt or response) or `training` (water to train one model) |
| `scope` | `fleet`, `site`, `other_sites`, `cloud_region`, `geographic_region`, `regulatory_average`; for AI rows `median_prompt`, `average_prompt`, `typical_response`, `estimate` or `model_lifetime` |
| `facility_or_region` | The site, region or population the figure describes |
| `country` | ISO 3166-1 alpha-2 code where the figure is for one country |
| `period` | Calendar or fiscal year |
| `wue_l_per_kwh` | WUE as published (`wue` rows) |
| `withdrawal_million_gal`, `discharge_million_gal`, `consumption_million_gal` | As published (`site_volume` rows); consumption = withdrawal − discharge |
| `consumption_million_litres` | Derived: consumption × 3.785411784 |
| `source_title`, `source_url`, `source_date`, `retrieved` | Where and when the figure was read |
| `notes` | Quotes, definitions and caveats |
| `energy_wh_per_prompt` | Energy per prompt in Wh, where the publisher gives it (`per_prompt` rows) |
| `water_ml_per_prompt` | Water per prompt or response in mL (`per_prompt` rows); OpenAI's 0.000085 US gallons is given as 0.32 |
| `water_million_litres` | Water in million litres (`training` rows) |
| `water_scope` | What the AI water figure counts: on-site cooling only, cooling plus electricity generation, or the full life cycle |

## Read before comparing

- **WUE definitions differ slightly.** AWS counts water *withdrawn* per kWh of IT load; Microsoft counts water used for humidification and cooling; the EU average counts total water input and excludes sites that report zero water (dry cooling), which pushes it up.
- **Site water is only part of the story.** Power stations use water too. That upstream water is not in any of these figures; the calculator on the page above adds it from WRI/WSP (2020) grid factors.
- **Litres are not impact.** The same volume matters far more in a water-stressed basin. Check a site's basin in WRI Aqueduct.
- **AI per-prompt figures are not like for like.** They differ by about 170 times mainly because they count different things: Google's 0.26 mL is on-site cooling water only, Li et al. add the water used to generate the electricity and assume 4 Wh per response, and Mistral's 45 mL is a full life cycle including server manufacturing. OpenAI has not said what its 0.32 mL covers. Compare `water_scope` and `energy_wh_per_prompt` before comparing values.
- **Correction (v2026.10.12.1).** Earlier versions said Meta publishes no data center water figures. That was wrong: Meta's 2025 Environmental Data Index gives annual data center WUE (0.19 L/kWh in 2024) and water withdrawal and consumption by site. Meta's rows are added in this version.

## Licence and citation

The compilation is released under **CC BY 4.0**. The figures are facts published by the organisations named in each row; cite them as well as this dataset.

Cite as: Say, J. (2026). *Data Center Water Benchmarks* (Version 2026.10.12.1) [Data set]. GreenCalculus. https://doi.org/10.5281/zenodo.23290085

Corrections: open an issue on this repository with the row id and the source.
