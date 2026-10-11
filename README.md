# Data Center Water Benchmarks

Publicly disclosed data center water figures, each traced to its publisher: water usage effectiveness (WUE) by operator and region, and yearly water withdrawal, discharge and consumption by site.

- **71 rows** from 6 publishers: Google (water by data center location, 2025: 40 named sites, other sites and the total), Amazon Web Services (global and 17 cloud regions, 2025), Microsoft (global and 3 regions, FY24 and FY25), Equinix and Digital Realty (portfolio WUE, 2025), and the European Commission (EU average WUE, 2024).
- **Each value is copied exactly** as the publisher printed it. The only derived column is `consumption_million_litres` (US gallons × 3.785411784).
- **Retrieved 11 October 2026.** Every row records its source URL and the table or document it came from.

Interactive version with a data center water calculator: https://greencalculus.com/data/data-center-water-usage/

## Columns

| Column | Meaning |
|---|---|
| `id` | Row id, stable within a version |
| `publisher` | Who published the figure |
| `metric` | `wue` (litres per kWh of IT energy) or `site_volume` (million US gallons per year) |
| `scope` | `fleet`, `site`, `other_sites`, `cloud_region`, `geographic_region` or `regulatory_average` |
| `facility_or_region` | The site, region or population the figure describes |
| `country` | ISO 3166-1 alpha-2 code where the figure is for one country |
| `period` | Calendar or fiscal year |
| `wue_l_per_kwh` | WUE as published (`wue` rows) |
| `withdrawal_million_gal`, `discharge_million_gal`, `consumption_million_gal` | As published (`site_volume` rows); consumption = withdrawal − discharge |
| `consumption_million_litres` | Derived: consumption × 3.785411784 |
| `source_title`, `source_url`, `source_date`, `retrieved` | Where and when the figure was read |
| `notes` | Quotes, definitions and caveats |

## Read before comparing

- **WUE definitions differ slightly.** AWS counts water *withdrawn* per kWh of IT load; Microsoft counts water used for humidification and cooling; the EU average counts total water input and excludes sites that report zero water (dry cooling), which pushes it up.
- **Site water is only part of the story.** Power stations use water too. That upstream water is not in any of these figures; the calculator on the page above adds it from WRI/WSP (2020) grid factors.
- **Litres are not impact.** The same volume matters far more in a water-stressed basin. Check a site's basin in WRI Aqueduct.
- **Absence is information.** Meta's 2025 Sustainability Report and its data-center pages publish no WUE or water volumes, so Meta has no row.

## Licence and citation

The compilation is released under **CC BY 4.0**. The figures are facts published by the organisations named in each row; cite them as well as this dataset.

Cite as: Say, J. (2026). *Data Center Water Benchmarks* (Version 2026.10.11) [Data set]. GreenCalculus.

Corrections: open an issue on this repository with the row id and the source.
