"""Geography: a light world outline file for the page and figures (Natural Earth 1:50m countries, simplified), each
country's region, and the region of every historical place (the country polygon it falls in, or the nearest one for
places on the coast) and every UN city (its ISO3 code)."""
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND", "SOL": "SOM"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, polys, isos, REG = [], [], [], {}
for f in W50["features"]:
    p = f["properties"]; iso = FIX.get(iso_of(p), iso_of(p))
    if p["SUBREGION"] == "Antarctica":
        continue
    g = shape(f["geometry"])
    reg = ISO_REGION_FIX.get(iso, SUB_REGION.get(p["SUBREGION"]))
    if reg is None:
        continue
    REG.setdefault(iso, reg)
    polys.append(g); isos.append(iso)
    gs = g.simplify(0.07, preserve_topology=True)
    if gs.is_empty:
        continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
TREE = STRtree(polys)


def region_at(lat, lon):
    pt = Point(lon, lat)
    hit = [i for i in TREE.query(pt) if polys[i].contains(pt)]
    if hit:
        return REG[isos[hit[0]]], isos[hit[0]], 0.0
    i = int(TREE.nearest(pt))
    return REG[isos[i]], isos[i], float(polys[i].distance(pt))


P = pd.read_pickle(f"{WORK}/places.pkl")
r = [region_at(a, b) for a, b in zip(P.lat, P.lon)]
P["reg"] = [x[0] for x in r]; P["iso"] = [x[1] for x in r]; P["off"] = [x[2] for x in r]
assert P.off.max() < 1.5, P.sort_values("off").tail(3)[["name", "lat", "lon", "off"]]
pd.to_pickle(P, f"{WORK}/places.pkl")

U = pd.read_pickle(f"{WORK}/un.pkl")
miss = sorted(set(U.ISO3_Code) - set(REG))
for iso in miss:      # small territories not in the 1:50m file: use the polygon nearest to their cities
    g = U[U.ISO3_Code == iso].iloc[0]; REG[iso] = region_at(g.PWCent_Latitude, g.PWCent_Longitude)[0]
U["reg"] = U.ISO3_Code.map(REG)
assert U.reg.notna().all()
pd.to_pickle(U, f"{WORK}/un.pkl")
X = pd.read_pickle(f"{WORK}/modern2000.pkl")
X["reg"] = [region_at(a, b)[0] for a, b in zip(X.lat, X.lon)]
pd.to_pickle(X, f"{WORK}/modern2000.pkl")
print("countries", len(feats), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB; places by region",
      P.reg.value_counts().sort_index().tolist(), "; UN territories filled", len(miss))
