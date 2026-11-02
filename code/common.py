"""Shared paths, regions and helpers for the largest-cities project.

Raw inputs (read in place from raw/, never modified):
  chandler.csv, chandlerV2.csv           Tertius Chandler's 1987 compilation (Four Thousand Years of Urban Growth),
                                          digitised and geocoded by Reba, Reitsma and Seto (2016); figshare
                                          10.6084/m9.figshare.2059494.v3, CC BY 4.0. V2 is used; V1 is read only to
                                          report what changed.
  modelskiAncient.csv, modelskiAncientV2.csv   George Modelski's World Cities (2003), ancient and classical cities,
                                          3700 BC to AD 1000; figshare 10.6084/m9.figshare.2059497.v2, CC BY 4.0.
  modelskiModern.csv, modelskiModernV2.csv     Modelski's cities of a million or more in AD 2000;
                                          figshare 10.6084/m9.figshare.2059500.v3, CC BY 4.0.
  chandler_meta.json, meta_2059497.json, meta_2059500.json   figshare metadata (DOIs, licences, file ids).
      All three: Reba, M., Reitsma, F. and Seto, K. C. (2016) Spatializing 6,000 years of global urbanization from
      3700 BC to AD 2000. Scientific Data 3, 160034. doi:10.1038/sdata.2016.34. The CSVs are Windows-1252 text.
  WUP2025-F18-DEGURBA-100_Largest_Cities.xlsx                 UN World Urbanization Prospects 2025, file 18
  WUP2025-F19-DEGURBA-100_Largest_Cities_in_2025_by_time.xlsx file 19
  WUP2025-F20-DEGURBA-Capital_Cities.xlsx                     file 20
  WUP2025-F21-DEGURBA-Cities_Pop.xlsx                         file 21 (every city of 50,000 or more, 1975 to 2050)
      United Nations, Department of Economic and Social Affairs, Population Division (2025). World Urbanization
      Prospects: The 2025 Revision. CC BY 3.0 IGO. Cities defined by the Degree of Urbanisation (DEGURBA).
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_50m_land.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("LC_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("LC_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("LC_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("LCTMP", "/dev/shm/largestcities"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "largest-cities"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23872999"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/largest-cities/"          # filled in by the publisher
REBA_DOI = "10.1038/sdata.2016.34"
FIG = {"chandler": "10.6084/m9.figshare.2059494.v3", "ancient": "10.6084/m9.figshare.2059497.v2", "modern": "10.6084/m9.figshare.2059500.v3"}
WUP_URL = "https://population.un.org/wup/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
TITLE = "The largest city on Earth"
SUBTITLE = "Six thousand years of the world's biggest cities, from Uruk to Dhaka"
PAPER_TITLE = "The Largest City on Earth: Six Thousand Years of the World's Biggest Cities, 3700 BC to AD 2050"
UN_FIRST, UN_LAST = 1975, 2050  # 1975 onwards is the UN; before that Chandler and Modelski
TOPN = 25                       # cities in the centre of gravity (also reported for the top 10)

# Regions, from Natural Earth's UN subregion of the country a city sits in (Iran and Afghanistan moved to West and
# Central Asia, where their history belongs). Order = legend order.
REGIONS = [("West and Central Asia", "#C8322B"), ("North Africa", "#E0A11B"), ("Europe", "#2F5FA7"), ("South Asia", "#7B57A8"),
           ("East Asia", "#2E9A8C"), ("South-East Asia and Oceania", "#D46A8C"), ("Sub-Saharan Africa", "#8A5A2B"),
           ("North America", "#1F2F4D"), ("Latin America and the Caribbean", "#6E8B3D")]
REG_SHORT = ["W & C Asia", "N Africa", "Europe", "S Asia", "E Asia", "SE Asia & Oceania", "Sub-Saharan Africa", "N America", "Latin America"]
SUB_REGION = {"Western Asia": 0, "Central Asia": 0, "Northern Africa": 1, "Northern Europe": 2, "Western Europe": 2, "Southern Europe": 2,
              "Eastern Europe": 2, "Southern Asia": 3, "Eastern Asia": 4, "South-Eastern Asia": 5, "Australia and New Zealand": 5,
              "Melanesia": 5, "Micronesia": 5, "Polynesia": 5, "Eastern Africa": 6, "Middle Africa": 6, "Southern Africa": 6,
              "Western Africa": 6, "Northern America": 7, "Caribbean": 8, "Central America": 8, "South America": 8}
ISO_REGION_FIX = {"IRN": 0, "AFG": 0, "SDN": 6, "SSD": 6, "CYP": 2, "GRL": 7}

# Snapshot dates. Before AD 1000: Modelski's grid plus the dates Chandler gives cross-sections for (1360, 650 and
# 430 BC; AD 361 and 622). AD 1100 to 1970: Chandler's benchmark years. 1975 to 2050: the UN, every five years.
# Years BC are negative; there is no year 0 (AD 1 follows 1 BC).
SNAP_ANCIENT = [-3700, -3500, -3300, -3000, -2800, -2500, -2400, -2300, -2200, -2100, -2000, -1900, -1800, -1700, -1600, -1500,
                -1400, -1360, -1300, -1200, -1100, -1000, -900, -800, -700, -650, -600, -500, -430, -400, -300, -200, -100,
                1, 100, 200, 300, 361, 400, 500, 600, 622, 700, 800, 900, 1000]
SNAP_CHANDLER = [1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1825, 1850, 1875,
                 1900, 1914, 1925, 1950, 1970]
SNAP_UN = list(range(1975, 2051, 5))
SNAPS = SNAP_ANCIENT + SNAP_CHANDLER + SNAP_UN
# Longest gap (years) across which one of Chandler's estimates for a city is interpolated to a snapshot date
# (log-linear between his two nearest dated estimates). Modelski's grid is never bridged: a gap there means the
# city was not on his list at that date.
CH_GAP = [(1000, 300), (1800, 200), (9999, 100)]


def ch_gap(y):
    return next(g for lim, g in CH_GAP if y <= lim)


def yfmt(y, short=False):
    """-430 -> '430 BC', 1850 -> 'AD 1850' (or '1850' when short and y >= 1000)."""
    y = int(y)
    if y < 0: return f"{-y:,} BC".replace(",", "")
    if short and y >= 1000: return str(y)
    return f"AD {y}"


def ydiff(a, b):
    """Years from a to b with no year 0."""
    return b - a - (1 if a < 0 < b else 0)


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{round(float(v) / 1000):,}"
    if f == "m1": return f"{float(v) / 1e6:.1f}"
    if f == "m2": return f"{float(v) / 1e6:.2f}"
    if f == "yr": return yfmt(v)
    if f == "yrs": return yfmt(v, short=True)
    raise ValueError(f)


def hav(lat1, lon1, lat2, lon2):
    import numpy as np
    a, b, c, d = map(np.radians, (lat1, lon1, lat2, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((c - a) / 2) ** 2 + np.cos(a) * np.cos(c) * np.sin((d - b) / 2) ** 2))


def short_un(name):
    """UN DEGURBA names carry the local form and the English one: 'Tōkyō (Tokyo)' -> 'Tokyo'."""
    m = re.search(r"\(([^()]+)\)\s*$", name)
    return dash(m.group(1) if m else name)
