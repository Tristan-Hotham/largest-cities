# The largest city on Earth: six thousand years of the world's biggest cities

Which city was the largest in the world at each moment from 3700 BC to the UN's projections for 2050, how big it was, and how the centre of the world's big cities moved: from Mesopotamia to Central Asia, out to the North Atlantic in the industrial age and back to Asia. Built from Reba, Reitsma and Seto's (2016) geocoded versions of Chandler's and Modelski's compilations (1,654 places, 10,033 estimates after cleaning) and the UN World Urbanization Prospects 2025 (16,828 cities, 1975 to 2050).

Interactive page: https://maps.tristanhotham.com/largest-cities/
Paper: https://doi.org/10.5281/zenodo.23872999
Blog post: https://blog.tristanhotham.com/2026/10/31/largest-cities/

## Headline results

- The crown: 30 different cities are the largest on their own at the 85 snapshots. Uruk leads from 3500 to 2800 BC (80,000 people); then Sumerian, Egyptian and Mesopotamian cities, Linzi, Alexandria, Rome (AD 1 to 400), Constantinople, Ctesiphon, Chang'an, Baghdad, Kaifeng, Merv, Hangzhou, Nanjing, Beijing, Istanbul, London (1850 to 1914), New York, Tokyo (1970 to 2005), Jakarta (2015 to 2045) and Dhaka (2050). Ties are reported as ties.
- Size: the largest city first reaches 100,000 in 2100 BC (Ur) and a million in 100 BC (Alexandria, in Modelski's figures). Between 1100 and 1750 the largest never exceeds 900,000. Jakarta has 41.9 million in 2025 (UN); Dhaka is projected at 52.1 million in 2050, 0.7% ahead of Jakarta.
- London: second to Beijing in 1800, 1.1% behind in 1825, largest from 1850 to 1914, level with New York in 1925 (0.4% apart); about 1826 to 1925 by interpolation.
- Centre of gravity (population-weighted, 25 largest): between 33 and 51 °E until 800 BC; between 59 and 82 °E from AD 500 to 1825; 60°N 4.9°W in 1900; 31°N 95°E in 2025.
- Counts: 1 city of a million in 1800, 16 in 1900 (compilations, floors); 165 in 1975, 511 in 2025 and 611 in 2050 (UN).
- Uncertainty: the two compilations name different leaders at 10 of 15 comparable snapshots (AD 1000: Baghdad 1,500,000 in Modelski, 125,000 in Chandler). The 1975 seam changes rankings: New York 17.1 million (Chandler) against 12.1 million (UN DEGURBA).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/places.csv` | The 1,654 historical places: name, other names, country, coordinates, region, certainty, sources, linked UN city code. |
| `data/estimates.csv` | Every population estimate after corrections (place, source, year, population). |
| `data/corrections.csv` | The 26 corrections made to the V2 files, with reasons. |
| `data/snapshots.csv` | Each place's estimate at each snapshot (combined, Modelski, Chandler, interpolated flag), and UN cities of 300,000 or more from 1975. |
| `data/largest_city.csv` | Per snapshot: the largest place, the runner-up, each compilation's leader, counts over 100,000 and a million, and the centre of gravity of the 25 and 10 largest. |
| `data/reigns.csv` | Runs of consecutive snapshots with the same leader. |
| `data/region_share_top25.csv` | Share of the 25 largest places' population by region, per snapshot. |
| `data/un_largest_2050.csv` | The UN's 100 largest cities of 2050 with 1975, 2000, 2025 and 2050 populations. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/world.json` | Page data. |
| `raw/` | The input files as downloaded (figshare CSVs and metadata, UN WUP 2025 files 18 to 21). |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- V2 files of Reba et al. (Chandler; Modelski ancient; Modelski modern), read as Windows-1252. V2 differs from V1 only in trimmed names, "Instanbul" to Istanbul, Kiev to Ukraine and two duplicate rows merged; no figure changes.
- Corrections: Modelski's American cities carry exact copies of their AD figures 1,300 years early in the BC columns (14 dropped); single factor-of-ten slips, figures on the wrong city and two misplaced locations fixed; zeros dropped.
- Snapshots: Modelski's grid to AD 1000 plus Chandler's cross-sections, Chandler's benchmark years 1100 to 1970, then the UN every five years 1975 to 2050. Chandler interpolated log-linearly across gaps of up to 300 years (before 1000), 200 (to 1800), 100 (after); Modelski only between adjacent grid dates; nothing extrapolated. Combined = mean of the compilations that give a figure. Ties within 0.5%.
- From 1975: UN WUP 2025, cities by the Degree of Urbanisation. The seam is reported, not smoothed.
- Centre of gravity: population-weighted mean of unit vectors of the 25 (and 10) largest places.
- Caveats: estimates, often rounded; the compilations disagree; coverage is thin for the Americas and sub-Saharan Africa; Modelski's 100,000 threshold creates ties; counts before 1975 are floors; 2030 to 2050 are projections.

## How to rerun

Needs Python 3 with numpy, pandas, openpyxl, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read from `raw/`; Natural Earth from `/home/claude/newdata/raw/geo/` (paths in `code/common.py`). Intermediate files go to `/dev/shm/largestcities/work` (set `LCTMP` to change).

```
python3 code/01_clean.py        # read and correct the compilations and the UN files
python3 code/02_geo.py          # outlines and regions
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Reba, M., Reitsma, F. and Seto, K. C. (2016) Spatializing 6,000 years of global urbanization from 3700 BC to AD 2000. Scientific Data 3, 160034. https://doi.org/10.1038/sdata.2016.34. Data on figshare, CC BY 4.0: https://doi.org/10.6084/m9.figshare.2059494.v3, https://doi.org/10.6084/m9.figshare.2059497.v2, https://doi.org/10.6084/m9.figshare.2059500.v3.
- Chandler, T. (1987) Four Thousand Years of Urban Growth: An Historical Census. Modelski, G. (2003) World Cities: -3000 to 2000.
- United Nations, Department of Economic and Social Affairs, Population Division (2025) World Urbanization Prospects: The 2025 Revision, files 18 to 21. CC BY 3.0 IGO.
- Natural Earth countries and land (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) The largest city on Earth: six thousand years of the world's biggest cities, 3700 BC to AD 2050. Zenodo. https://doi.org/10.5281/zenodo.23872999

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
