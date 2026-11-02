"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, un, L, n, RG, T, CG = R["source"], R["un"], R["london"], R["n"], R["reign"], R["txt"], R["cog_sum"]
N = lambda v: f"{round(v):,}"
M = lambda v: f"{v / 1e6:.1f}"
readme = f"""# The largest city on Earth: six thousand years of the world's biggest cities

Which city was the largest in the world at each moment from 3700 BC to the UN's projections for 2050, how big it was, and how the centre of the world's big cities moved: from Mesopotamia to Central Asia, out to the North Atlantic in the industrial age and back to Asia. Built from Reba, Reitsma and Seto's (2016) geocoded versions of Chandler's and Modelski's compilations ({N(s['places'])} places, {N(s['estimates'])} estimates after cleaning) and the UN World Urbanization Prospects 2025 ({N(s['un_cities'])} cities, 1975 to 2050).

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- The crown: {R['n_crown_sole']} different cities are the largest on their own at the {s['n_snaps']} snapshots. Uruk leads from 3500 to 2800 BC ({N(RG['Uruk']['peak'])} people); then Sumerian, Egyptian and Mesopotamian cities, Linzi, Alexandria, Rome (AD 1 to 400), Constantinople, Ctesiphon, Chang'an, Baghdad, Kaifeng, Merv, Hangzhou, Nanjing, Beijing, Istanbul, London (1850 to 1914), New York, Tokyo (1970 to 2005), Jakarta (2015 to 2045) and Dhaka (2050). Ties are reported as ties.
- Size: the largest city first reaches 100,000 in {yfmt(R['size']['first_100k']['y'])} (Ur) and a million in {yfmt(R['size']['first_1m']['y'])} (Alexandria, in Modelski's figures). Between 1100 and 1750 the largest never exceeds {N(R['size']['max_1100_1750'])}. Jakarta has {M(un['jakarta2025'])} million in 2025 (UN); Dhaka is projected at {M(un['dhaka2050'])} million in 2050, {un['dhaka_margin_2050_pct']}% ahead of Jakarta.
- London: second to Beijing in 1800, {L['gap1825_pct']}% behind in 1825, largest from 1850 to 1914, level with New York in 1925 ({L['gap1925_pct']}% apart); about {L['cross_in']} to {L['cross_out']} by interpolation.
- Centre of gravity (population-weighted, {TOPN} largest): between {T['meso_lon_min']:.0f} and {T['meso_lon_max']:.0f} °E until 800 BC; between {T['lon500_1825_min']:.0f} and {T['lon500_1825_max']:.0f} °E from AD 500 to 1825; {CG['c1900']['lat']:.0f}°N {T['c1900_lon']:.1f}°{T['c1900_hem']} in 1900; {CG['c2025']['lat']:.0f}°N {CG['c2025']['lon']:.0f}°E in 2025.
- Counts: {n['m1_1800']} city of a million in 1800, {n['m1_1900']} in 1900 (compilations, floors); {n['m1_1975']} in 1975, {n['m1_2025']} in 2025 and {n['m1_2050']} in 2050 (UN).
- Uncertainty: the two compilations name different leaders at {R['n_disagree']} of {R['n_both']} comparable snapshots (AD 1000: Baghdad {N(R['baghdad1000']['m'])} in Modelski, {N(R['baghdad1000']['c'])} in Chandler). The 1975 seam changes rankings: New York {M(R['seam_sum']['ny_ch'])} million (Chandler) against {M(R['seam_sum']['ny_un'])} million (UN DEGURBA).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/places.csv` | The {N(s['places'])} historical places: name, other names, country, coordinates, region, certainty, sources, linked UN city code. |
| `data/estimates.csv` | Every population estimate after corrections (place, source, year, population). |
| `data/corrections.csv` | The {s['fixes']} corrections made to the V2 files, with reasons. |
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
- Corrections: Modelski's American cities carry exact copies of their AD figures 1,300 years early in the BC columns ({s['americas_copies']} dropped); single factor-of-ten slips, figures on the wrong city and two misplaced locations fixed; zeros dropped.
- Snapshots: Modelski's grid to AD 1000 plus Chandler's cross-sections, Chandler's benchmark years 1100 to 1970, then the UN every five years 1975 to 2050. Chandler interpolated log-linearly across gaps of up to 300 years (before 1000), 200 (to 1800), 100 (after); Modelski only between adjacent grid dates; nothing extrapolated. Combined = mean of the compilations that give a figure. Ties within {s['tie_pct']}%.
- From 1975: UN WUP 2025, cities by the Degree of Urbanisation. The seam is reported, not smoothed.
- Centre of gravity: population-weighted mean of unit vectors of the {TOPN} (and 10) largest places.
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

- Reba, M., Reitsma, F. and Seto, K. C. (2016) Spatializing 6,000 years of global urbanization from 3700 BC to AD 2000. Scientific Data 3, 160034. https://doi.org/{REBA_DOI}. Data on figshare, CC BY 4.0: https://doi.org/{FIG['chandler']}, https://doi.org/{FIG['ancient']}, https://doi.org/{FIG['modern']}.
- Chandler, T. (1987) Four Thousand Years of Urban Growth: An Historical Census. Modelski, G. (2003) World Cities: -3000 to 2000.
- United Nations, Department of Economic and Social Affairs, Population Division (2025) World Urbanization Prospects: The 2025 Revision, files 18 to 21. CC BY 3.0 IGO.
- Natural Earth countries and land (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) The largest city on Earth: six thousand years of the world's biggest cities, 3700 BC to AD 2050. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The historical population data are
derived from Reba, M., Reitsma, F. and Seto, K. C. (2016), Spatializing 6,000
years of global urbanization from 3700 BC to AD 2000, Scientific Data 3, 160034
(data on figshare, CC BY 4.0), which digitises Chandler (1987) and Modelski
(2003). The modern data are derived from United Nations, Department of Economic
and Social Affairs, Population Division (2025), World Urbanization Prospects:
The 2025 Revision, CC BY 3.0 IGO. Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] The largest city on Earth for 6,000 years: from Uruk ({N(RG['Uruk']['peak'])} people) to Jakarta ({M(un['jakarta2025'])} million), and the path of the urban world's centre from Mesopotamia to the Arctic and back to Asia

## Body

I combined the two classic compilations of historical city sizes (Chandler and Modelski, as geocoded by Reba, Reitsma and Seto in 2016) with the UN's new World Urbanization Prospects 2025 to find the largest city at {s['n_snaps']} dates from 3700 BC to 2050. {R['n_crown_sole']} different cities have held the crown. Uruk led for seven centuries; Rome from AD 1 to 400; Chinese capitals (Kaifeng, Hangzhou, Nanjing, Beijing) in {T['china_n']} of {T['china_of']} snapshots between 1100 and 1825, never above {N(R['size']['max_1100_1750'])} people until 1800; London from about {L['cross_in']} to {L['cross_out']}; then New York, Tokyo and, under the UN's new definition, Jakarta. Dhaka is projected to edge past Jakarta in {un['dhaka_first']}. The line is the population-weighted centre of the {TOPN} largest cities: it sits over Central Asia for 1,300 years, swings out over the North Atlantic in the industrial age (the centre of points spread round the globe goes north), and is now over Tibet. Caveats: pre-modern figures are estimates and the two compilations disagree at {R['n_disagree']} of {R['n_both']} comparable dates; the Americas and Africa are thinly covered; 1975 onwards uses a different definition of a city (no blending). Interactive map with a time slider and each city's history: {PAGE}

## Source comment

Sources: Reba, Reitsma and Seto (2016), Scientific Data 3:160034, data on figshare (CC BY 4.0), from Chandler (1987) and Modelski (2003); United Nations World Urbanization Prospects 2025, files 18 to 21 (CC BY 3.0 IGO), cities by the Degree of Urbanisation. Outlines: Natural Earth. I fixed {s['fixes']} errors in the source files (listed in the paper).

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
assert RG["Uruk"]["last"] - RG["Uruk"]["first"] == 700 and RG["Rome"]["first"] == 1   # "Uruk led for seven centuries"
assert T["lon500_1825_max"] > 60 and 1825 - 500 == 1325                                # "over Central Asia for 1,300 years"
for t in (readme, post, lic):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
