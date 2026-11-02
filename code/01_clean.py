"""Read the Reba et al. (2016) compilations (Chandler, Modelski ancient, Modelski modern; V2 files) and the UN World
Urbanization Prospects 2025 DEGURBA files; record what changed between V1 and V2; apply a short list of documented
corrections; merge Chandler's and Modelski's entries for the same place; write intermediates to WORK.

Decoding: the CSVs are Windows-1252, not UTF-8 or Latin-1. Bytes 0x8A, 0x9A and 0x91 (Š, š and a curly
apostrophe) are control characters in Latin-1, so names such as Šiauliai come out wrong unless cp1252 is used.

Corrections (each logged in WORK/checks.json and listed in the paper):
  * zero populations are treated as missing;
  * Modelski's cities in the Americas carry, in the BC columns, an exact copy of their AD figures shifted 1,300 years
    earlier (Teotihuacan 900 BC = AD 400, Caracol 700 BC = AD 600, Tollan 300 BC = AD 1000 and so on): the BC copies
    are dropped;
  * single values that are out by a factor of about ten from the same city's neighbouring estimates (an extra or a
    missing digit): Philadelphia 1914, Algiers 1925, Nanjing 1970, Palermo 1150, Delhi 1375; and Modelski's Montevideo
    in 2000 (13.3 million);
  * values attached to the wrong city: Memphis (Egypt) in 1975 is Memphis, Tennessee's figure; Gelibolu's AD 1000 and
    1200 figures repeat Constantinople's exactly; London in 100 BC predates the Roman foundation;
  * two locations: Modelski's Shangqi is geocoded on Shanghai and is moved to Shangqiu, Henan; his Caracol is geocoded
    on El Caracol at Chichen Itza and is moved to Caracol, Belize, the Maya city his AD 400 to 800 figures describe;
  * rows with the same name less than 5 km apart are one city (Brasov, Gwalior).
"""
import numpy as np, pandas as pd
from common import *

CHK = {}


def read(fn):
    raw = open(f"{RAW}/{fn}", "rb").read()
    try:
        raw.decode("utf-8"); utf8 = True
    except UnicodeDecodeError:
        utf8 = False
    df = pd.read_csv(f"{RAW}/{fn}", encoding="cp1252", dtype=str, keep_default_na=False)
    return df, utf8, raw


def col_year(c):
    return (-1 if c.startswith("BC") else 1) * int(c[3:])


# ---------- V1 versus V2 ----------
diff = {}
for key, (a, b) in {"chandler": ("chandler.csv", "chandlerV2.csv"), "ancient": ("modelskiAncient.csv", "modelskiAncientV2.csv"),
                    "modern": ("modelskiModern.csv", "modelskiModernV2.csv")}.items():
    A, ua, rawa = read(a); B, ub, rawb = read(b)
    assert not ua and not ub                                     # neither file is valid UTF-8
    sp = lambda d: int((d.City != d.City.str.strip()).sum() + (d.Country != d.Country.str.strip()).sum())
    sA, sB = A.apply(lambda s: s.str.strip()), B.apply(lambda s: s.str.strip())
    d = {"v1_rows": len(A), "v2_rows": len(B), "cols_same": list(A.columns) == list(B.columns), "v1_padded": sp(A), "v2_padded": sp(B),
         "names_only_v1": sorted(set(sA.City) - set(sB.City)), "names_only_v2": sorted(set(sB.City) - set(sA.City))}
    m = sA.merge(sB, on=["City", "Latitude"], suffixes=("1", "2"))
    d["country_changes"] = m[m.Country1 != m.Country2][["City", "Country1", "Country2"]].values.tolist()
    # values added or changed, matching rows by trimmed name and country
    ka = sA.City + "|" + sA.Country; kb = sB.City + "|" + sB.Country
    vc = list(B.columns[6:])
    # rows with the same key are combined (V1 has Guadalajara twice and 'Madgdeburg' beside Magdeburg)
    fix = lambda k: k.replace("Madgdeburg", "Magdeburg")
    melt = lambda s, k: {(kk, c, v) for kk, row in zip(k, s[vc].values) for c, v in zip(vc, row) if v}
    la, lb = melt(sA, ka.map(fix)), melt(sB, kb)
    keys = set(ka.map(fix)) & set(kb)
    d["value_changes"] = sorted([[k.split("|")[0], c, v, "v1" if t in la - lb else "v2"] for t in (la ^ lb) for k, c, v in [t] if k in keys])
    d["dup_rows_v1"] = sA[ka.duplicated(keep=False)].City.unique().tolist(); d["dup_rows_v2"] = sB[kb.duplicated(keep=False)].City.unique().tolist()
    d["cp1252_bytes"] = sorted({hex(c) for c in rawb if 0x80 <= c <= 0x9F})
    diff[key] = d
CHK["v1_v2"] = diff
dc = diff["chandler"]
assert (dc["v1_rows"], dc["v2_rows"]) == (1599, 1597) and dc["names_only_v1"] == ["Madgdeburg"]
assert dc["country_changes"] == [["Kiev", "Russian Federation", "Ukraine"]]
assert diff["ancient"]["names_only_v1"] == ["Instanbul"] and diff["ancient"]["names_only_v2"] == ["Istanbul"]
assert dc["v1_padded"] > 50 and dc["v2_padded"] <= 2
# once V1's two Guadalajara rows and its misspelt "Madgdeburg" row are combined, no figure differs between V1 and V2
assert dc["value_changes"] == [] and "Guadalajara" in dc["dup_rows_v1"] and "Guadalajara" not in dc["dup_rows_v2"]
assert all(d["value_changes"] == [] for d in diff.values())
# names that need cp1252 (Latin-1 would turn these bytes into control characters)
C0 = read("chandlerV2.csv")[0]
CHK["cp1252_names"] = sorted({n.strip() for n in pd.concat([C0.City, C0.OtherName]) if any(ch in n for ch in "ŠšŽž‘’")})
assert CHK["cp1252_names"], "expected a few names with cp1252-only characters"
# a few alternative names lost characters before the files were written (stored as "?"), e.g. Soltaniyeh's Persian forms
CHK["lost_char_names"] = sorted(C0.City[C0.OtherName.str.contains(r"\?")].str.strip())
assert len(CHK["lost_char_names"]) == 3


# ---------- long tables of estimates ----------
def long(df, src):
    df = df.apply(lambda s: s.str.strip())
    yc = [c for c in df.columns if re.fullmatch(r"(BC|AD)_\d+", c)]
    rows = []
    for i, r in df.iterrows():
        for c in yc:
            if r[c] != "":
                rows.append((src, i, col_year(c), int(float(r[c]))))
    meta = df[["City", "OtherName", "Country", "Latitude", "Longitude", "Certainty"]].copy()
    meta["lat"] = meta.Latitude.astype(float); meta["lon"] = meta.Longitude.astype(float); meta["cert"] = meta.Certainty.astype(int)
    meta["src"] = src; meta["row"] = meta.index
    return meta.drop(columns=["Latitude", "Longitude", "Certainty"]), pd.DataFrame(rows, columns=["src", "row", "year", "pop"])


CM, CE = long(read("chandlerV2.csv")[0], "C")
MM, ME = long(read("modelskiAncientV2.csv")[0], "M")
XM, XE = long(read("modelskiModernV2.csv")[0], "X")
CHK["raw"] = {"chandler_rows": len(CM), "chandler_values": len(CE), "ancient_rows": len(MM), "ancient_values": len(ME),
              "modern_rows": len(XM), "modern_values": len(XE), "chandler_cols": int(CE.year.nunique()), "ancient_cols": int(ME.year.nunique()),
              "chandler_first": int(CE.year.min()), "chandler_last": int(CE.year.max()), "ancient_first": int(ME.year.min()), "ancient_last": int(ME.year.max()),
              "cert_chandler": {int(k): int(v) for k, v in CM.cert.value_counts().items()}, "cert_ancient": {int(k): int(v) for k, v in MM.cert.value_counts().items()},
              "modern_min": int(XE["pop"].min())}
assert CHK["raw"]["ancient_first"] == -3700 and CHK["raw"]["ancient_last"] == 1000 and CHK["raw"]["chandler_last"] == 1975

fixes = []


def drop(E, M, src, city, year, why, country=None):
    rows = M[(M.City == city) & ((M.Country == country) if country else True)].row
    sel = (E.src == src) & E.row.isin(rows) & (E.year == year)
    assert sel.sum() == 1, (city, year, sel.sum())
    fixes.append({"src": src, "city": city, "year": int(year), "value": int(E[sel]["pop"].iloc[0]), "why": why})
    return E[~sel]


# zeros
z = {"C": int((CE["pop"] <= 0).sum()), "M": int((ME["pop"] <= 0).sum()), "X": int((XE["pop"] <= 0).sum())}
CE, ME = CE[CE["pop"] > 0], ME[ME["pop"] > 0]
CHK["zeros"] = z
# Modelski's Americas: BC values that duplicate the AD values 1,300 years later
AMER = MM[(MM.lon < -30)]
mir, unmir = [], []
for _, r in AMER.iterrows():
    e = ME[ME.row == r.row]; ad = dict(zip(e.year, e["pop"]))
    for y, v in zip(e.year, e["pop"]):
        if y < 0:
            (mir if ad.get(y + 1300) == v else unmir).append((r.City, int(y), int(v)))
assert not unmir and len(mir) == 14, (unmir, len(mir))
dropidx = ME.row.isin(AMER.row) & (ME.year < 0)
for c, y, v in mir:
    fixes.append({"src": "M", "city": c, "year": y, "value": v, "why": "copy of the AD figure 1,300 years later"})
ME = ME[~dropidx]
CHK["americas_bc_copies"] = len(mir)
# factor-of-ten slips and values attached to the wrong city
for city, year, why, cty in (("Philadelphia", 1914, "ten times the 1900 and 1925 figures (an extra digit)", None),
                             ("Algiers", 1925, "sixteen times 1900 and five times 1950 (an extra digit)", None),
                             ("Nanjing", 1970, "a fifth of 1950 and a tenth of 1975 (a missing digit)", None),
                             ("Palermo", 1150, "125 people between 90,000 and 150,000", None),
                             ("Delhi", 1375, "ten times the 1354 and 1398 figures (an extra digit)", None),
                             ("Memphis", 1975, "the figure for Memphis, Tennessee", "Egypt"),
                             ("Gelibolu", 1000, "repeats Constantinople's figure", None),
                             ("Gelibolu", 1200, "repeats Constantinople's figure", None),
                             ("London", -100, "before the Roman foundation of London", "United Kingdom")):
    CE = drop(CE, CM, "C", city, year, why, cty)
XE = drop(XE, XM, "X", "Montevideo", 2000, "ten times the city's population (an extra digit)")
assert {f["city"] for f in fixes if f["src"] == "C"} >= {"Philadelphia", "Memphis", "Gelibolu"}
# locations
for M_, city, lat, lon, why in ((MM, "Shangqi", 34.41, 115.65, "geocoded on Shanghai; moved to Shangqiu, Henan"),
                                (MM, "Caracol", 16.763, -89.117, "geocoded on El Caracol, Chichen Itza; moved to Caracol, Belize")):
    i = M_.index[M_.City == city]; assert len(i) == 1
    fixes.append({"src": "M", "city": city, "year": None, "value": None, "why": why, "from": [float(M_.loc[i[0], "lat"]), float(M_.loc[i[0], "lon"])]})
    M_.loc[i, "lat"] = lat; M_.loc[i, "lon"] = lon
CHK["fixes"] = fixes

# ---------- one record per place ----------
alln = lambda r: {norm(x) for x in [r.City] + re.split(r"[,;/]", r.OtherName) if norm(x)}
# same name, < 5 km: one city (within a source)
for M_, E_ in ((CM, CE),):
    merged = []
    for nm, g in M_.groupby("City"):
        if len(g) < 2: continue
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g.iloc[i], g.iloc[j]
                if hav(a.lat, a.lon, b.lat, b.lon) < 5:
                    merged.append((nm, int(a.row), int(b.row)))
    CHK["same_name_merged"] = [m[0] for m in merged]
    for nm, ra, rb in merged:
        E_.loc[(E_.src == "C") & (E_.row == rb), "row"] = ra
        M_.drop(M_.index[M_.row == rb], inplace=True)
CE = CE.groupby(["src", "row", "year"], as_index=False)["pop"].mean()
CE["pop"] = CE["pop"].round().astype(int)
assert sorted(CHK["same_name_merged"]) == ["Brasov", "Gwalior"]

# Chandler and Modelski entries for the same place: same name (or alternative name) and < 30 km apart, plus three pairs
# named differently in the two lists.
PAIRS = {"Pataliputra": "Patna", "Yin": "Anyang"}
cities = []   # one dict per place
cid = {}
for _, r in CM.iterrows():
    cid[("C", r.row)] = len(cities)
    cities.append({"name": r.City, "alt": r.OtherName, "country": r.Country, "lat": r.lat, "lon": r.lon, "cert": int(r.cert), "srcs": "C", "names": alln(r)})
match = []
for _, r in MM.iterrows():
    best = None
    for i, c in enumerate(cities):
        d = hav(r.lat, r.lon, c["lat"], c["lon"])
        if d < 30 and (alln(r) & c["names"] or PAIRS.get(r.City) == c["name"]):
            if best is None or d < best[1]:
                best = (i, d)
    if best:
        c = cities[best[0]]; c["srcs"] += "M"; c["cert_m"] = int(r.cert); cid[("M", r.row)] = best[0]
        match.append((r.City, c["name"], round(best[1], 1)))
        if r.City != c["name"] and r.City not in c["alt"]:
            c["alt"] = (c["alt"] + ", " if c["alt"] else "") + r.City
    else:
        cid[("M", r.row)] = len(cities)
        cities.append({"name": r.City, "alt": r.OtherName, "country": r.Country, "lat": r.lat, "lon": r.lon, "cert": int(r.cert), "srcs": "M", "names": alln(r)})
CHK["matched_modelski_chandler"] = len(match)
assert ("Pataliputra", "Patna", 0.3) in match and any(m[0] == "Xian" for m in match) and any(m[0] == "Istanbul" for m in match)
E = pd.concat([CE, ME])
E["cid"] = [cid[(s, r)] for s, r in zip(E.src, E.row)]
E = E[["cid", "src", "year", "pop"]].sort_values(["cid", "src", "year"]).reset_index(drop=True)
CT = pd.DataFrame(cities).drop(columns=["names"])
CT["cert_m"] = CT.get("cert_m")
CHK["places"] = len(CT); CHK["estimates"] = len(E)

# Modelski modern (2000): kept separately for the comparison of definitions
X = XM.merge(XE, on="row")[["City", "Country", "lat", "lon", "cert", "pop"]]

# ---------- UN WUP 2025 ----------
U = pd.read_excel(f"{RAW}/WUP2025-F21-DEGURBA-Cities_Pop.xlsx", "Data")
U.columns = [int(c) if str(c).isdigit() else c for c in U.columns]
YRS = [c for c in U.columns if isinstance(c, int)]
assert YRS[0] == UN_FIRST and YRS[-1] == UN_LAST and len(YRS) == 76
for y in YRS:
    U[y] = U[y] * 1000.0          # thousands to people
F18 = pd.read_excel(f"{RAW}/WUP2025-F18-DEGURBA-100_Largest_Cities.xlsx", "Data")
F19 = pd.read_excel(f"{RAW}/WUP2025-F19-DEGURBA-100_Largest_Cities_in_2025_by_time.xlsx", "Data")
F20 = pd.read_excel(f"{RAW}/WUP2025-F20-DEGURBA-Capital_Cities.xlsx", "Data")
# the files agree: F18's ranks equal F21's ordering, F19's 2025 list equals F21's top 100 in 2025
for y in SNAP_UN:
    top = U.nlargest(100, y)
    f = F18[F18.Year == y].sort_values("Rank_Order")
    assert list(f.City_Code) == list(top.City_Code), y
    assert np.allclose(f.Population.values * 1000, top[y].values, rtol=1e-6)
assert set(F19[F19.Year == 2025].City_Code) == set(U.nlargest(100, 2025).City_Code)
plaus = F18.groupby("City_Code").Pop_plausibility.agg(lambda s: s.mode().iloc[0]).to_dict()
U["plaus"] = U.City_Code.map(plaus)
U["short"] = U.City_Name.map(short_un)
CHK["un"] = {"cities": len(U), "years": len(YRS), "f18_rows": len(F18), "f19_rows": len(F19), "f20_rows": len(F20),
             "plaus_counts": {k: int(v) for k, v in F18.Pop_plausibility.value_counts().items()}}

pd.to_pickle(CT, f"{WORK}/places.pkl"); pd.to_pickle(E, f"{WORK}/est.pkl"); pd.to_pickle(X, f"{WORK}/modern2000.pkl")
pd.to_pickle(U, f"{WORK}/un.pkl"); pd.to_pickle(F18, f"{WORK}/f18.pkl"); pd.to_pickle(F20, f"{WORK}/f20.pkl")
jsave(CHK, f"{WORK}/checks.json", indent=1)
print("places", len(CT), "estimates", len(E), "matched", len(match), "fixes", len(fixes), "UN cities", len(U))
print("cp1252 names", CHK["cp1252_names"][:8])
