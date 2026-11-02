"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json).

Method (also in the paper):
  * snapshots: Modelski's dates 3700 BC to AD 1000 plus Chandler's cross-section years (SNAPS in common.py), then the UN
    every five years from 1975 to 2050;
  * a place's estimate at a snapshot, from each compilation separately: its own figure for that year; otherwise, for
    Chandler, a log-linear interpolation between his two nearest dated figures for that place if they are no more than
    CH_GAP years apart (300 before AD 1000, 200 to 1800, 100 after); for Modelski, only between two neighbouring dates of
    his grid (a blank in his grid means the place was not on his list then). Nothing is extrapolated;
  * combined estimate before 1975: the mean of the two compilations where both give one, otherwise the one there is;
  * largest city: the highest combined estimate; places within 0.5% of the top are reported as tied;
  * from 1975: UN WUP 2025, cities defined by the Degree of Urbanisation (DEGURBA). The seam is not smoothed;
  * centre of gravity: the population-weighted mean position of the 25 (and 10) largest places at each snapshot,
    averaged as unit vectors on the sphere."""
import numpy as np, pandas as pd
from common import *

P = pd.read_pickle(f"{WORK}/places.pkl"); E = pd.read_pickle(f"{WORK}/est.pkl"); U = pd.read_pickle(f"{WORK}/un.pkl")
X = pd.read_pickle(f"{WORK}/modern2000.pkl"); F20 = pd.read_pickle(f"{WORK}/f20.pkl"); CHK = jload(f"{WORK}/checks.json")
RN = [r for r, _ in REGIONS]
R = {}
MGRID = sorted(E[E.src == "M"].year.unique())
assert set(MGRID) <= set(SNAP_ANCIENT) and len(MGRID) == 41
HIST = SNAP_ANCIENT + SNAP_CHANDLER

# ---------- names: the modern place name, with the period name the text uses ----------
DISPLAY = {"Sao Paolo": "São Paulo", "Xian": "Xi'an", "Anyang": "Yin", "Patna": "Patna", "Kanauji": "Kannauj", "Taxilla": "Taxila", "Mohenjodaro": "Mohenjo-daro"}
PERIOD = {"Istanbul": [(1453, "Constantinople")], "Xian": [(1300, "Chang'an")], "Tokyo": [(1868, "Edo")], "Patna": [(700, "Pataliputra")],
          "Mexico City": [(1521, "Tenochtitlan")], "Anyang": [(-1000, "Yin")], "Beijing": [], "Nanjing": [], "Cairo": [(969, "Fustat")]}
P["disp"] = [DISPLAY.get(n, n) for n in P.name]
P["cert"] = [int(min(a, b)) if b == b and b is not None else int(a) for a, b in zip(P.cert, P.cert_m)]   # the more confident of the two scores


def andjoin(xs):
    xs = list(xs)
    return "" if not xs else xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def name_at(i, y):
    n = P.name[i]
    for until, nm in PERIOD.get(n, []):
        if y < until: return nm
    return P.disp[i]


# ---------- estimates at snapshots ----------
ser = {(c, s): (g.year.values, g["pop"].values.astype(float)) for (c, s), g in E.groupby(["cid", "src"])}


def est(c, s, t):
    if (c, s) not in ser: return None
    y, v = ser[(c, s)]; i = int(np.searchsorted(y, t))
    if i < len(y) and y[i] == t: return float(v[i]), 0
    if i == 0 or i == len(y): return None
    y0, y1, v0, v1 = y[i - 1], y[i], v[i - 1], v[i]
    if s == "M":
        j = MGRID.index(y0)
        if j + 1 >= len(MGRID) or MGRID[j + 1] != y1: return None
    elif ydiff(y0, y1) > ch_gap(t):
        return None
    f = ydiff(y0, t) / ydiff(y0, y1)
    return float(np.exp(np.log(v0) + f * (np.log(v1) - np.log(v0)))), 1


SN = {}      # year -> DataFrame(cid, pop, m, c, interp)
for t in HIST:
    rows = []
    for c in P.index:
        m, ch = est(c, "M", t), est(c, "C", t)
        if m or ch:
            vals = [x[0] for x in (m, ch) if x]
            rows.append((c, float(np.mean(vals)), m[0] if m else np.nan, ch[0] if ch else np.nan, int(any(x and x[1] for x in (m, ch)))))
    SN[t] = pd.DataFrame(rows, columns=["cid", "pop", "m", "c", "interp"]).sort_values("pop", ascending=False).reset_index(drop=True)

# ---------- UN cities, and links from historical places to them ----------
U = U.reset_index(drop=True)
U5 = {y: U[["City_Code", y]].dropna() for y in SNAP_UN}
link = {}
for i, p in P.iterrows():
    d = hav(p.lat, p.lon, U.PWCent_Latitude.values, U.PWCent_Longitude.values)
    names = {norm(x) for x in [p["name"]] + re.split(r"[,;/]", p["alt"] or "") if norm(x)}
    best = None
    for j in np.where(d < 50)[0]:
        un = {norm(U.short[j]), norm(U.City_Name[j])} | {norm(x) for x in re.split(r"[()]", U.City_Name[j]) if norm(x)}
        if any(a == b or (len(a) >= 4 and f" {a} " in f" {b} ") for a in names for b in un):
            if best is None or U.at[j, 2025] > U.at[best, 2025] or np.isnan(U.at[best, 2025]):
                best = j
    if best is not None:
        link[i] = best
P["un"] = [link.get(i, -1) for i in P.index]
# a UN city linked from two places keeps the bigger one only (e.g. two Chandler rows inside one DEGURBA city)
dup = P[P.un >= 0].groupby("un").filter(lambda g: len(g) > 1)
for u, g in dup.groupby("un"):
    keep = g.index[np.argmax([E[E.cid == c]["pop"].max() for c in g.index])]
    for c in g.index:
        if c != keep: P.at[c, "un"] = -1
R["links"] = {"n": int((P.un >= 0).sum()), "shared_dropped": int(len(dup) - dup.un.nunique())}
for nm in ("London", "Tokyo", "New York", "Beijing", "Istanbul", "Xian", "Baghdad", "Cairo"):
    j = P[P.name == nm].un.iloc[0] if nm != "London" else P[(P.name == "London") & (P.country == "United Kingdom")].un.iloc[0]
    assert j >= 0, nm
assert P[P.name == "Uruk"].un.iloc[0] == -1 and P[P.name == "Babylon"].un.iloc[0] == -1

# ---------- largest at each snapshot ----------
TIE = 0.005


def leaders(df, col="pop"):
    d = df.dropna(subset=[col]).sort_values(col, ascending=False)
    if not len(d): return [], 0
    mx = d[col].iloc[0]
    return list(d[d[col] >= mx * (1 - TIE)].cid), float(mx)


uid = lambda code: int(U.index[U.City_Code == code][0])
SNAPROWS = []
for t in HIST:
    d = SN[t]; L, mx = leaders(d); Lm, mm = leaders(d, "m"); Lc, mc = leaders(d, "c")
    top = d.head(TOPN)
    SNAPROWS.append({"y": t, "era": "M" if t <= 1000 else "C", "lead": L, "pop": mx, "n": len(d), "second": int(d.cid.iloc[len(L)]) if len(d) > len(L) else None,
                     "second_pop": float(d["pop"].iloc[len(L)]) if len(d) > len(L) else None, "lead_m": Lm, "pop_m": mm, "lead_c": Lc, "pop_c": mc,
                     "n100k": int((d["pop"] >= 1e5).sum()), "n1m": int((d["pop"] >= 1e6).sum()), "top": [int(x) for x in top.cid], "toppop": [float(x) for x in top["pop"]]})
for t in SNAP_UN:
    d = U[["City_Code", t]].dropna().sort_values(t, ascending=False)
    mx = d[t].iloc[0]; L = [("u", int(c)) for c in d[d[t] >= mx * (1 - TIE)].City_Code]
    top = d.head(TOPN)
    SNAPROWS.append({"y": t, "era": "U", "lead": L, "pop": float(mx), "n": len(d), "second": ("u", int(d.City_Code.iloc[len(L)])), "second_pop": float(d[t].iloc[len(L)]),
                     "n100k": int((d[t] >= 1e5).sum()), "n1m": int((d[t] >= 1e6).sum()), "top": [("u", int(c)) for c in top.City_Code], "toppop": [float(x) for x in top[t]]})

# a single id space: historical places 0..n-1, then UN cities not linked to any of them
NP = len(P)
un2id = {int(U.City_Code[j]): int(i) for i, j in zip(P.index, P.un) if j >= 0}
show_un = set()
for t in SNAP_UN:
    show_un |= set(U.City_Code[U[t] >= 3e5].astype(int))
show_un |= set(un2id)
extra = [c for c in U.City_Code.astype(int) if c in show_un and c not in un2id]
for k, c in enumerate(extra):
    un2id[c] = NP + k
ID = lambda x: un2id[x[1]] if isinstance(x, tuple) else int(x)
UNROW = {int(c): j for j, c in enumerate(U.City_Code.astype(int))}


def cname(i, y=2025):
    if i < NP and y >= UN_FIRST and P.un[i] >= 0: return U.short[int(P.un[i])]    # modern names in the UN era (Kolkata, not Calcutta)
    if i < NP: return name_at(i, y)
    return U.short[UNROW[extra[i - NP]]]


def creg(i):
    return int(P.reg[i]) if i < NP else int(U.reg[UNROW[extra[i - NP]]])


def cll(i):
    if i < NP and P.un[i] < 0: return float(P.lat[i]), float(P.lon[i])
    j = UNROW[extra[i - NP]] if i >= NP else int(P.un[i])
    return (float(P.lat[i]), float(P.lon[i])) if i < NP else (float(U.PWCent_Latitude[j]), float(U.PWCent_Longitude[j]))


for s in SNAPROWS:
    s["lead"] = [ID(x) for x in s["lead"]]; s["top"] = [ID(x) for x in s["top"]]
    if s["second"] is not None: s["second"] = ID(s["second"])
    for k in ("lead_m", "lead_c"):
        if k in s: s[k] = [int(x) for x in s[k]]
SR = {s["y"]: s for s in SNAPROWS}

# ---------- reigns: runs of snapshots with the same leader (a tie is its own state) ----------
reigns = []
for s in SNAPROWS:
    key = tuple(sorted(s["lead"]))
    if reigns and reigns[-1]["key"] == key:
        reigns[-1]["last"] = s["y"]; reigns[-1]["n"] += 1; reigns[-1]["peak"] = max(reigns[-1]["peak"], s["pop"])
    else:
        reigns.append({"key": key, "first": s["y"], "last": s["y"], "n": 1, "peak": s["pop"], "era": s["era"]})
for r in reigns:
    r["ids"] = list(r["key"]); r["tie"] = len(r["key"]) > 1
    r["names"] = sorted(cname(i, r["first"]) for i in r["key"]); r["reg"] = creg(r["key"][0])
    r["label"] = andjoin(r["names"])
    r["first_t"], r["last_t"] = yfmt(r["first"], True), yfmt(r["last"], True)
    del r["key"]
R["reigns"] = reigns
crown_ids = sorted({i for r in reigns if not r["tie"] for i in r["ids"]})
R["crown_cities"] = [cname(i) for i in crown_ids]
R["n_reigns"] = len(reigns); R["n_crown_cities"] = len(crown_ids)
sole = [r for r in reigns if not r["tie"]]
# the expected succession appears (the period name is used in reigns)
labels = [r["label"] for r in reigns]
for nm in ("Uruk", "Memphis", "Babylon", "Rome", "Constantinople", "Chang'an", "Baghdad", "Kaifeng", "Hangzhou", "Beijing", "London", "New York", "Tokyo", "Jakarta", "Dhaka"):
    assert any(nm == l for l in labels), (nm, labels)


def reign(nm, k=0):
    rs = [r for r in reigns if r["label"] == nm]
    return rs[k]


def snap(y): return SR[y]


def lead_name(y): s = snap(y); return andjoin(cname(i, y) for i in s["lead"])


# named facts used in the text
RG = {}
for nm in ("Uruk", "Memphis", "Babylon", "Rome", "Constantinople", "Chang'an", "Baghdad", "Kaifeng", "Hangzhou", "Beijing", "London", "New York", "Tokyo", "Jakarta", "Dhaka", "Istanbul", "Nanjing", "Alexandria", "Linzi", "Girsu", "Ur", "Thebes", "Pi-Ramesses", "Merv", "Lagash", "Mari", "Eridu", "Larsa", "Yin", "Avaris", "Nineveh", "Ctesiphon"):
    rs = [r for r in reigns if r["label"] == nm]
    if rs:
        RG[nm.replace("'", "").replace(" ", "_")] = {"first": rs[0]["first"], "last": rs[-1]["last"], "n_runs": len(rs), "n": sum(r["n"] for r in rs),
                                                    "peak": max(r["peak"] for r in rs), "first_t": yfmt(rs[0]["first"], True), "last_t": yfmt(rs[-1]["last"], True),
                                                    "runs": [[r["first"], r["last"]] for r in rs]}
R["reign"] = RG
assert RG["Uruk"]["first"] == -3500 and RG["Uruk"]["last"] == -2800 and RG["Memphis"]["first"] == -2000 and RG["Memphis"]["n"] == 1
assert RG["London"]["first"] == 1850 and RG["London"]["last"] == 1914 and RG["New_York"]["first"] == 1950 and RG["New_York"]["last"] == 1950
assert any(r["label"] == "London and New York" and r["first"] == 1925 for r in reigns) and any(r["label"] == "Jakarta and Tokyo" and r["first"] == 2010 for r in reigns)
assert RG["Tokyo"]["first"] == 1970 and RG["Tokyo"]["last"] == 2005 and RG["Jakarta"]["first"] == 2015 and RG["Jakarta"]["last"] == 2045 and RG["Dhaka"]["first"] == 2050
assert RG["Rome"]["first"] == 1 and RG["Rome"]["last"] == 400 and RG["Beijing"]["n_runs"] == 2

# ---------- ties ----------
ties = [r for r in reigns if r["tie"]]
R["ties"] = [{"first": r["first"], "last": r["last"], "names": r["names"], "pop": r["peak"]} for r in ties]
R["n_tie_snaps"] = sum(r["n"] for r in ties)
assert any(set(t["names"]) >= {"Thebes", "Memphis", "Babylon"} for t in R["ties"])

# ---------- where the two compilations disagree ----------
dis = []
for s in SNAPROWS:
    if s["era"] != "U":
        s["nm"] = int(SN[s["y"]].m.notna().sum()); s["nc"] = int(SN[s["y"]].c.notna().sum())
    # compared only where each compilation has at least eight places at that date
    if s["era"] == "U" or not s["lead_m"] or not s["lead_c"] or min(s["nm"], s["nc"]) < 8: continue
    if not set(s["lead_m"]) & set(s["lead_c"]):
        dis.append({"y": s["y"], "m": [cname(i, s["y"]) for i in s["lead_m"]], "pm": s["pop_m"], "c": [cname(i, s["y"]) for i in s["lead_c"]], "pc": s["pop_c"],
                    "comb": [cname(i, s["y"]) for i in s["lead"]], "pop": s["pop"]})
both = [s for s in SNAPROWS if s["era"] != "U" and s["lead_m"] and s["lead_c"] and min(s["nm"], s["nc"]) >= 8]
R["disagree"] = dis; R["n_both"] = len(both); R["n_disagree"] = len(dis)
b1000 = snap(1000)
R["baghdad1000"] = {"m": est(P.index[P.name == "Baghdad"][0], "M", 1000)[0], "c": est(P.index[P.name == "Baghdad"][0], "C", 1000)[0],
                    "comb": b1000["pop"], "c_lead": cname(b1000["lead_c"][0], 1000), "c_lead_pop": b1000["pop_c"]}
assert R["baghdad1000"]["m"] == 1.5e6 and R["baghdad1000"]["c"] == 125000 and R["baghdad1000"]["c_lead"] == "Cordoba"
bg = P.index[P.name == "Baghdad"][0]
R["baghdad_peak_c"] = {"y": 932, "pop": float(ser[(bg, "C")][1][list(ser[(bg, "C")][0]).index(932)])}

# ---------- how big the biggest has been ----------
first = lambda thr, key="pop": next(s for s in SNAPROWS if s[key] >= thr)
R["size"] = {}
for thr, k in ((1e5, "100k"), (1e6, "1m"), (1e7, "10m"), (2e7, "20m")):
    s = first(thr); R["size"]["first_" + k] = {"y": s["y"], "city": lead_name(s["y"]), "pop": s["pop"], "era": s["era"]}
for src, key, lk in (("m", "pop_m", "lead_m"), ("c", "pop_c", "lead_c")):
    for thr, k in ((1e5, "100k"), (1e6, "1m")):
        s = next((s for s in SNAPROWS if s.get(key, 0) >= thr), None)
        R["size"][f"first_{k}_{src}"] = {"y": s["y"], "city": andjoin(cname(i, s["y"]) for i in s[lk]), "pop": s[key]} if s else None
R["size"]["max_hist"] = max(SNAPROWS[:len(HIST)], key=lambda s: s["pop"])["pop"]
R["size"]["y2025"] = snap(2025)["pop"]; R["size"]["y2050"] = snap(2050)["pop"]; R["size"]["y1975"] = snap(1975)["pop"]; R["size"]["y1970"] = snap(1970)["pop"]
R["size"]["y1800"] = snap(1800)["pop"]; R["size"]["y1900"] = snap(1900)["pop"]; R["size"]["y1000"] = snap(1000)["pop"]; R["size"]["y100"] = snap(100)["pop"]
R["size"]["x1800_2025"] = round(R["size"]["y2025"] / R["size"]["y1800"], 1)
R["size"]["x1900_2025"] = round(R["size"]["y2025"] / R["size"]["y1900"], 1)
assert R["size"]["first_1m_m"]["city"] == "Alexandria" and R["size"]["first_1m_m"]["y"] == -100
assert R["size"]["first_100k"]["city"] == "Ur" and R["size"]["first_100k"]["y"] == -2100
# the largest place never passes a million between AD 1000 and 1800 (in the combined estimates)
R["size"]["max_1100_1750"] = max(s["pop"] for s in SNAPROWS if 1100 <= s["y"] <= 1750)
assert R["size"]["max_1100_1750"] < 1e6

# ---------- how many cities passed 100,000 and a million ----------
R["counts"] = [{"y": s["y"], "era": s["era"], "n100k": s["n100k"], "n1m": s["n1m"], "n": s["n"]} for s in SNAPROWS]
cn = {s["y"]: s for s in SNAPROWS}
ch1975 = E[(E.src == "C") & (E.year == 1975)]
R["n"] = {k: cn[y][f] for k, y, f in (("m1_1800", 1800, "n1m"), ("m1_1850", 1850, "n1m"), ("m1_1900", 1900, "n1m"), ("m1_1950", 1950, "n1m"), ("m1_1975", 1975, "n1m"),
                                     ("m1_2025", 2025, "n1m"), ("m1_2050", 2050, "n1m"), ("k100_1000", 1000, "n100k"), ("k100_1500", 1500, "n100k"), ("k100_1800", 1800, "n100k"),
                                     ("k100_1900", 1900, "n100k"), ("k100_1975", 1975, "n100k"), ("k100_2025", 2025, "n100k"), ("k100_2050", 2050, "n100k"),
                                     ("k100_100", 100, "n100k"), ("k100_m1000", -1000, "n100k"), ("m1_100", 100, "n1m"))}
R["n"]["ch1975_m1"] = int((ch1975["pop"] >= 1e6).sum()); R["n"]["ch1975_rows"] = int(len(ch1975)); R["n"]["ch1975_min"] = int(ch1975["pop"].min())
R["n"]["m10_2025"] = int((U[2025] >= 1e7).sum()); R["n"]["m10_1975"] = int((U[1975] >= 1e7).sum()); R["n"]["m10_2050"] = int((U[2050] >= 1e7).sum())
R["n"]["m20_2025"] = int((U[2025] >= 2e7).sum())
R["n"]["un_cities_2025"] = int(U[2025].notna().sum()); R["n"]["un_pop_2025"] = float(U[2025].sum())
R["n"]["m1_first_two"] = [s["y"] for s in SNAPROWS if s["n1m"] >= 2][0]
R["n"]["un2000_m1"] = int((U[2000] >= 1e6).sum()); R["n"]["mod2000_m1"] = int(len(X))
assert R["n"]["mod2000_m1"] == 292 and R["n"]["m1_1800"] == 1

# ---------- centre of gravity ----------
def centre(ids, pops):
    ll = np.array([cll(i) for i in ids]); w = np.array(pops)
    la, lo = np.radians(ll[:, 0]), np.radians(ll[:, 1])
    v = np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]) * w[:, None]
    s = v.sum(0); s /= np.linalg.norm(s)
    return float(np.degrees(np.arcsin(s[2]))), float(np.degrees(np.arctan2(s[1], s[0])))


COG = []
for s in SNAPROWS:
    a = centre(s["top"], s["toppop"]); b = centre(s["top"][:10], s["toppop"][:10])
    COG.append({"y": s["y"], "lat": round(a[0], 2), "lon": round(a[1], 2), "lat10": round(b[0], 2), "lon10": round(b[1], 2), "n": len(s["top"])})
R["cog"] = COG
CG = {c["y"]: c for c in COG}
east = max(COG, key=lambda c: c["lon"]); west = min(COG, key=lambda c: c["lon"])
R["cog_sum"] = {"east": east, "west": west, "c1000": CG[1000], "c1500": CG[1500], "c1800": CG[1800], "c1900": CG[1900], "c1950": CG[1950], "c2025": CG[2025],
                "c2050": CG[2050], "c_m3000": CG[-3000], "c_m500": CG[-500], "c100": CG[100], "c1975": CG[1975], "c1700": CG[1700], "c1250": CG[1250]}
R["cog_sum"]["west_y"] = west["y"]
# distance travelled by the top-25 centre: 1800 to 1900 (west), 1950 to 2025 (east)
R["cog_sum"]["km_1800_1900"] = round(float(hav(CG[1800]["lat"], CG[1800]["lon"], CG[1900]["lat"], CG[1900]["lon"])))
R["cog_sum"]["km_1950_2025"] = round(float(hav(CG[1950]["lat"], CG[1950]["lon"], CG[2025]["lat"], CG[2025]["lon"])))
assert -5 < CG[1900]["lon"] < 40 and CG[2025]["lon"] > 75 and CG[-3000]["lon"] > 40 and CG[1500]["lon"] > 60

# ---------- regions of the 25 largest ----------
REGS = []
for s in SNAPROWS:
    sh = np.zeros(len(RN))
    for i, p in zip(s["top"], s["toppop"]): sh[creg(i)] += p
    REGS.append({"y": s["y"], "share": [round(100 * x / sh.sum(), 2) for x in sh], "n": len(s["top"])})
R["regions"] = REGS
RS = {r["y"]: r for r in REGS}
nreg = lambda y, k: sum(1 for i in SR[y]["top"] if creg(i) == k)
R["reg_sum"] = {"eu_1900": RS[1900]["share"][2], "eu_1900_n": nreg(1900, 2), "eu_2025_n": nreg(2025, 2), "eu_2050_n": nreg(2050, 2), "na_1950_n": nreg(1950, 7),
                "ea_1500": RS[1500]["share"][4], "wa_m2500": RS[-2500]["share"][0], "ssa_2025_n": nreg(2025, 6), "ssa_2050_n": nreg(2050, 6),
                "sa_2050_n": nreg(2050, 3), "asia_2025_n": sum(nreg(2025, k) for k in (0, 3, 4, 5)), "asia_2050_n": sum(nreg(2050, k) for k in (0, 3, 4, 5)),
                "eu_1900_share": RS[1900]["share"][2], "asia_1800_n": sum(nreg(1800, k) for k in (0, 3, 4, 5)), "na_2025_n": nreg(2025, 7), "la_2025_n": nreg(2025, 8)}
assert R["reg_sum"]["eu_1900_n"] >= 12 and R["reg_sum"]["eu_2025_n"] <= 2

# ---------- London ----------
lon_i = P.index[(P.name == "London") & (P.country == "United Kingdom")][0]
rank = lambda y, i: SR[y]["top"].index(i) + 1 if i in SR[y]["top"] else None
lonrows = [{"y": y, "rank": rank(y, lon_i), "pop": float(SN[y].set_index("cid")["pop"].get(lon_i, np.nan)) if y in SN else None} for y in SNAP_CHANDLER]
bj = P.index[P.name == "Beijing"][0]; ny = P.index[P.name == "New York"][0]
g = lambda y, i: float(SN[y].set_index("cid")["pop"][i])
R["london"] = {"first": RG["London"]["first"], "last": RG["London"]["last"], "span": RG["London"]["last"] - RG["London"]["first"], "n": RG["London"]["n"],
               "p1825": g(1825, lon_i), "bj1825": g(1825, bj), "p1850": g(1850, lon_i), "bj1850": g(1850, bj), "p1800": g(1800, lon_i), "bj1800": g(1800, bj),
               "p1914": g(1914, lon_i), "ny1914": g(1914, ny), "p1925": g(1925, lon_i), "ny1925": g(1925, ny), "p1900": g(1900, lon_i), "ny1900": g(1900, ny),
               "p1950": g(1950, lon_i), "ny1950": g(1950, ny), "p1750": g(1750, lon_i), "p1700": g(1700, lon_i), "p1600": g(1600, lon_i),
               "rank1700": rank(1700, lon_i), "rank1500": rank(1500, lon_i), "rank1600": rank(1600, lon_i), "rank1750": rank(1750, lon_i),
               "rank1800": rank(1800, lon_i), "rank1950": rank(1950, lon_i), "rank1970": rank(1970, lon_i), "rows": lonrows}
L = R["london"]
L["gap1825_pct"] = round(100 * (L["bj1825"] - L["p1825"]) / L["bj1825"], 1); L["gap1925_pct"] = round(100 * (L["ny1925"] - L["p1925"]) / L["ny1925"], 1)
L["x1850"] = round(L["p1850"] / L["bj1850"], 2); L["x1900"] = round(L["p1900"] / L["ny1900"], 2)
# crossing years, linear in population between the bracketing snapshots (an estimate on estimates)
cross = lambda y0, y1, a0, a1, b0, b1: y0 + (y1 - y0) * (b0 - a0) / ((a1 - a0) - (b1 - b0))
L["cross_in"] = round(cross(1825, 1850, g(1825, lon_i), g(1850, lon_i), g(1825, bj), g(1850, bj)))
L["cross_out"] = round(cross(1914, 1925, g(1914, ny), g(1925, ny), g(1914, lon_i), g(1925, lon_i)))
L["years_est"] = L["cross_out"] - L["cross_in"]
lu = U.iloc[int(P.un[lon_i])]
L["un1975"] = float(lu[1975]); L["un2025"] = float(lu[2025]); L["un2050"] = float(lu[2050]); L["un_rank2025"] = int((U[2025] > lu[2025]).sum() + 1)
L["un_rank1975"] = int((U[1975] > lu[1975]).sum() + 1)
assert L["rank1800"] == 2 and L["ny1925"] > L["p1925"] and 1825 < L["cross_in"] < 1850 and 1914 < L["cross_out"] <= 1925 and L["gap1825_pct"] < 2

# ---------- the UN era and 2050 ----------
rk = {y: U[["City_Code", y]].dropna().sort_values(y, ascending=False).City_Code.astype(int).tolist() for y in (1975, 2000, 2025, 2050)}
cityrow = lambda code: U.iloc[UNROW[code]]
top = lambda y, n: [{"name": cityrow(c).short, "country": cityrow(c).Location, "pop": float(cityrow(c)[y]), "p1975": None if np.isnan(cityrow(c)[1975]) else float(cityrow(c)[1975]), "p2025": float(cityrow(c)[2025]), "p2050": float(cityrow(c)[2050]), "code": c, "reg": int(cityrow(c).reg), "plaus": cityrow(c).plaus} for c in rk[y][:n]]
R["un"] = {"top1975": top(1975, 10), "top2025": top(2025, 10), "top2050": top(2050, 10), "top2025_25": top(2025, 25), "top2050_25": top(2050, 25)}
for k in range(10):
    for y in (2025, 2050):
        c = R["un"][f"top{y}"][k]["code"]; R["un"][f"top{y}"][k]["rank_other"] = (rk[2050 if y == 2025 else 2025].index(c) + 1)
# the annual series: when the lead changed hands
annual = [y for y in range(UN_FIRST, UN_LAST + 1)]
lead_y = {y: int(U.loc[U[y].idxmax(), "City_Code"]) for y in annual}
code_of = lambda nm: int(U.City_Code[U.short == nm].iloc[0]) if nm != "London" else int(U.City_Code[(U.short == "London") & (U.ISO3_Code == "GBR")].iloc[0])
TK, JK, DK = code_of("Tokyo"), code_of("Jakarta"), code_of("Dhaka")
R["un"]["jakarta_first"] = next(y for y in annual if lead_y[y] == JK); R["un"]["dhaka_first"] = next(y for y in annual if lead_y[y] == DK)
R["un"]["dhaka_over_tokyo"] = next(y for y in annual if cityrow(DK)[y] > cityrow(TK)[y])
R["un"]["tokyo_peak_y"] = int(max(annual, key=lambda y: cityrow(TK)[y])); R["un"]["tokyo_peak"] = float(cityrow(TK)[R["un"]["tokyo_peak_y"]])
for nm, c in (("tokyo", TK), ("jakarta", JK), ("dhaka", DK)):
    for y in (1975, 2000, 2025, 2050):
        R["un"][f"{nm}{y}"] = float(cityrow(c)[y])
R["un"]["dhaka_margin_2050"] = R["un"]["dhaka2050"] - R["un"]["jakarta2050"]
R["un"]["dhaka_margin_2050_pct"] = round(100 * R["un"]["dhaka_margin_2050"] / R["un"]["jakarta2050"], 1)
R["un"]["plaus_jakarta"] = cityrow(JK).plaus; R["un"]["plaus_dhaka"] = cityrow(DK).plaus
assert R["un"]["jakarta_first"] == 2010 and R["un"]["dhaka_first"] == 2049 and R["un"]["dhaka_over_tokyo"] == 2022
# who rises: growth 2025 to 2050 among the 100 largest in 2050
g50 = U[U.City_Code.isin(rk[2050][:100])].copy()
g50["gain"] = g50[2050] - g50[2025]; g50["pct"] = 100 * (g50[2050] / g50[2025] - 1)
gainers = g50.sort_values("gain", ascending=False).head(15)
R["un"]["gainers"] = [{"name": r.short, "country": r.Location, "p2025": float(r[2025]), "p2050": float(r[2050]), "gain": float(r.gain), "pct": round(float(r.pct), 1),
                       "reg": int(r.reg), "r2025": rk[2025].index(int(r.City_Code)) + 1, "r2050": rk[2050].index(int(r.City_Code)) + 1} for _, r in gainers.iterrows()]
fast = g50[g50[2050] >= 1e7].sort_values("pct", ascending=False).head(10)
R["un"]["fastest10m"] = [{"name": r.short, "country": r.Location, "p2025": float(r[2025]), "p2050": float(r[2050]), "pct": round(float(r.pct), 1), "reg": int(r.reg)} for _, r in fast.iterrows()]
shrink = g50[g50.gain < 0].sort_values("gain").head(8)
R["un"]["shrinkers"] = [{"name": r.short, "country": r.Location, "p2025": float(r[2025]), "p2050": float(r[2050]), "gain": float(r.gain), "pct": round(float(r.pct), 1)} for _, r in shrink.iterrows()]
R["un"]["new_top10_2050"] = [d["name"] for d in R["un"]["top2050"] if d["code"] not in rk[2025][:10]]
R["un"]["out_top10_2050"] = [d["name"] for d in R["un"]["top2025"] if d["code"] not in rk[2050][:10]]
R["un"]["new_top25_2050"] = [d["name"] for d in R["un"]["top2050_25"] if d["code"] not in rk[2025][:25]]
R["un"]["gain_top100"] = float(g50.gain.sum()); R["un"]["n_shrink_top100"] = int((g50.gain < 0).sum())
ssa50 = g50[g50.reg == 6]; R["un"]["ssa_top100_2050"] = int(len(ssa50)); R["un"]["ssa_top100_2025"] = int(sum(1 for c in rk[2025][:100] if cityrow(c).reg == 6))
R["un"]["ssa_gain_share"] = round(100 * ssa50.gain.sum() / g50.gain.sum(), 1)
for nm in ("Lagos", "Kinshasa", "Karachi", "Hajipur", "Addis Ababa", "Al-Qahirah (Cairo)", "Dar es Salaam", "Luanda", "Shanghai", "New Delhi", "Seoul", "Ciudad de México (Mexico City)"):
    c = int(U.City_Code[U.City_Name == nm].iloc[0]) if nm in set(U.City_Name) else code_of(nm)
    k = norm(short_un(nm)).replace(" ", "_")
    R["un"][k] = {"p2025": float(cityrow(c)[2025]), "p2050": float(cityrow(c)[2050]), "r2025": rk[2025].index(c) + 1, "r2050": rk[2050].index(c) + 1}
assert R["un"]["lagos"]["r2050"] < R["un"]["lagos"]["r2025"] and R["un"]["new_top10_2050"] == ["Karachi"] and R["un"]["out_top10_2050"] == ["Seoul"] and R["un"]["gainers"][0]["name"] == "Dhaka"
# capitals among the ten largest (F21's Capital column)
cap = dict(zip(U.City_Code.astype(int), U.Capital))
R["un"]["capitals_top10_2025"] = int(sum(cap[d["code"]] == 1 for d in R["un"]["top2025"]))
R["un"]["f20_capitals"] = int(len(F20)); R["un"]["f20_city"] = int((F20.Type_of_Settlement == "City").sum())

# ---------- the seam: one place, two definitions ----------
seam = []
for _, r in ch1975.sort_values("pop", ascending=False).head(12).iterrows():
    i = int(r.cid); j = P.un[i]
    seam.append({"name": P.disp[i], "chandler1975": float(r["pop"]), "un1975": float(U.at[j, 1975]) if j >= 0 else None,
                 "un_rank1975": (rk[1975].index(int(U.City_Code[j])) + 1) if j >= 0 else None, "ch_rank": len(seam) + 1})
R["seam"] = seam
sm = {d["name"]: d for d in seam}
R["seam_sum"] = {"tokyo_ch": sm["Tokyo"]["chandler1975"], "tokyo_un": sm["Tokyo"]["un1975"], "ny_ch": sm["New York"]["chandler1975"], "ny_un": sm["New York"]["un1975"],
                 "ny_ratio": round(sm["New York"]["un1975"] / sm["New York"]["chandler1975"], 2), "ny_un_rank": sm["New York"]["un_rank1975"]}
# Jakarta and Dhaka in Chandler's 1975 list
for nm in ("Jakarta", "Dhaka"):
    q = P.index[P.name == nm]
    v = E[(E.cid.isin(q)) & (E.src == "C") & (E.year == 1975)]
    R["seam_sum"][norm(nm) + "_ch"] = float(v["pop"].iloc[0]) if len(v) else None
    R["seam_sum"][norm(nm) + "_ch_rank"] = int((ch1975["pop"] > v["pop"].iloc[0]).sum() + 1) if len(v) else None
R["seam_sum"]["jakarta_un"] = R["un"]["jakarta1975"]; R["seam_sum"]["jakarta_un_rank"] = rk[1975].index(JK) + 1
assert R["seam_sum"]["ny_un"] < R["seam_sum"]["ny_ch"] and sm["Tokyo"]["un_rank1975"] == 1
# Modelski's 2000 list against the UN's 2000 figures
xs = []
for _, r in X.sort_values("pop", ascending=False).iterrows():
    d = hav(r.lat, r.lon, U.PWCent_Latitude.values, U.PWCent_Longitude.values)
    j = int(np.nanargmax(np.where(d < 40, U[2000].fillna(0).values, -1))) if (d < 40).any() else None
    xs.append({"name": r.City, "mod": float(r["pop"]), "un": float(U.at[j, 2000]) if j is not None and d[j] < 40 else None, "un_name": U.short[j] if j is not None else None})
R["mod2000"] = {"top": xs[:10], "n": len(xs), "tokyo_mod": next(x["mod"] for x in xs if x["name"] == "Tokyo"), "n_matched": sum(1 for x in xs if x["un"])}
R["mod2000"]["un_bigger"] = sum(1 for x in xs if x["un"] and x["un"] > x["mod"]); R["mod2000"]["lead"] = xs[0]["name"]; R["mod2000"]["lead_pop"] = xs[0]["mod"]

# ---------- coverage: where the record is thin ----------
cov = []
ERA = [("Before 1000 BC", -9999, -1001), ("1000 BC to AD 999", -1000, 999), ("1000 to 1499", 1000, 1499), ("1500 to 1799", 1500, 1799), ("1800 to 1975", 1800, 1975)]
for k, rn in enumerate(RN):
    row = {"region": rn}
    for en, a, b in ERA:
        e = E[(E.year >= a) & (E.year <= b) & E.cid.isin(P.index[P.reg == k])]
        row[en] = int(e.cid.nunique())
    cov.append(row)
R["coverage"] = cov; R["eras"] = [e[0] for e in ERA]
CV = {c["region"]: c for c in cov}
R["thin"] = {"am_pre1000": sum(CV[r][e] for r in ("Latin America and the Caribbean", "North America") for e in ("Before 1000 BC", "1000 BC to AD 999")),
             "ssa_pre1000": CV["Sub-Saharan Africa"]["1000 BC to AD 999"] + CV["Sub-Saharan Africa"]["Before 1000 BC"], "ssa_1000_1499": CV["Sub-Saharan Africa"]["1000 to 1499"],
             "am_1000_1499": CV["Latin America and the Caribbean"]["1000 to 1499"] + CV["North America"]["1000 to 1499"],
             "eu_1500_1799": CV["Europe"]["1500 to 1799"], "ea_1500_1799": CV["East Asia"]["1500 to 1799"], "sa_1500_1799": CV["South Asia"]["1500 to 1799"],
             "ssa_1500_1799": CV["Sub-Saharan Africa"]["1500 to 1799"], "eu_1800": CV["Europe"]["1800 to 1975"], "places": len(P)}
americas_m = [P.disp[i] for i in P.index[(P.lon < -30) & P.srcs.str.contains("M")]]
R["thin"]["americas_modelski"] = sorted(americas_m)
# certainty of the leaders
cert = [int(P.cert[i]) for s in SNAPROWS if s["era"] != "U" for i in s["lead"]]
R["cert"] = {"lead_c1": sum(c == 1 for c in cert), "lead_n": len(cert), "lead_c23": sorted({cname(i) for s in SNAPROWS if s["era"] != "U" for i in s["lead"] if P.cert[i] > 1}),
             "c1": CHK["raw"]["cert_chandler"]["1"], "c2": CHK["raw"]["cert_chandler"]["2"], "c3": CHK["raw"]["cert_chandler"]["3"],
             "m1": CHK["raw"]["cert_ancient"]["1"], "m2": CHK["raw"]["cert_ancient"]["2"], "m3": CHK["raw"]["cert_ancient"]["3"],
             "vijay_cert": int(P.cert[P.index[P.name == "Vijayanagar"][0]]), "hangzhou_cert": int(P.cert[P.index[P.name == "Hangzhou"][0]])}
# interpolated shares
it = pd.concat([SN[t].head(10).assign(y=t) for t in HIST])
R["interp"] = {"top10_pct": round(100 * it.interp.mean(), 1), "lead_interp": sum(int(SN[t].interp.iloc[0]) for t in HIST)}

# ---------- source summary ----------
v12 = CHK["v1_v2"]
R["source"] = {"places": len(P), "estimates": len(E), "chandler_rows": CHK["raw"]["chandler_rows"], "chandler_values": CHK["raw"]["chandler_values"],
               "ancient_rows": CHK["raw"]["ancient_rows"], "ancient_values": CHK["raw"]["ancient_values"], "modern_rows": CHK["raw"]["modern_rows"],
               "chandler_cols": CHK["raw"]["chandler_cols"], "ancient_cols": CHK["raw"]["ancient_cols"], "matched": CHK["matched_modelski_chandler"],
               "chandler_first": CHK["raw"]["chandler_first"], "n_snaps": len(SNAPS), "n_hist_snaps": len(HIST), "n_un_snaps": len(SNAP_UN),
               "un_cities": CHK["un"]["cities"], "un_shown": len(show_un), "fixes": len(CHK["fixes"]), "americas_copies": CHK["americas_bc_copies"],
               "v1_rows": v12["chandler"]["v1_rows"], "v2_rows": v12["chandler"]["v2_rows"], "v1_padded": v12["chandler"]["v1_padded"] + v12["ancient"]["v1_padded"] + v12["modern"]["v1_padded"],
               "v2_padded": v12["chandler"]["v2_padded"] + v12["ancient"]["v2_padded"] + v12["modern"]["v2_padded"], "lost_chars": len(CHK["lost_char_names"]),
               "zeros": CHK["zeros"]["C"], "plaus": CHK["un"]["plaus_counts"], "tie_pct": TIE * 100, "topn": TOPN}
R["fixes"] = CHK["fixes"]; R["v1v2"] = v12; R["cp1252_names"] = CHK["cp1252_names"]; R["lost_char_names"] = CHK["lost_char_names"]
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG}
R["snaps"] = [{k: s[k] for k in ("y", "era", "pop", "n", "n100k", "n1m")} | {"lead": [cname(i, s["y"]) for i in s["lead"]], "second": cname(s["second"], s["y"]) if s["second"] is not None else None,
               "second_pop": s["second_pop"], "lead_m": [cname(i, s["y"]) for i in s.get("lead_m", [])], "pop_m": s.get("pop_m"), "lead_c": [cname(i, s["y"]) for i in s.get("lead_c", [])], "pop_c": s.get("pop_c")} for s in SNAPROWS]

# lookups for the text: every snapshot by year, and each crown city's peak in each compilation
R["S"] = {str(d["y"]): d for d in R["snaps"]}
pk = {}
for nm in ("Uruk", "Babylon", "Rome", "Istanbul", "Xian", "Baghdad", "Kaifeng", "Hangzhou", "Beijing", "London", "Alexandria", "Memphis", "Thebes", "Linzi", "Patna", "Ur", "Cordoba", "Ctesiphon", "Merv", "Nanjing", "New York", "Tokyo"):
    i = P.index[(P.name == nm) & ((P.country == "United Kingdom") if nm == "London" else True)][0]; d = {}
    for sname, key in (("M", "m"), ("C", "c")):
        if (i, sname) in ser:
            y, v = ser[(i, sname)]; k = int(np.argmax(v)); d[key + "_peak"] = float(v[k]); d[key + "_peak_y"] = int(y[k]); d[key + "_n"] = int(len(v))
            a = y <= 1000
            if a.any():
                k = int(np.argmax(np.where(a, v, -1))); d[key + "_peak1000"] = float(v[k]); d[key + "_peak1000_y"] = int(y[k])
    pk[norm(nm).replace(" ", "_")] = d
R["peak"] = pk
assert pk["rome"]["m_peak"] == 1.2e6 and pk["rome"]["m_peak_y"] == 200 and pk["rome"]["c_peak1000_y"] == 100
R["n_crown_sole"] = len({i for r in reigns if not r["tie"] for i in r["ids"]})

# ---------- small values the prose needs (ordinals, lists, counts over spans) ----------
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
ur_i = P.index[P.name == "Ur"][0]
T = {"c1900_lon": abs(CG[1900]["lon"]), "c1900_hem": "W" if CG[1900]["lon"] < 0 else "E",
     "cert_list": andjoin(R["cert"]["lead_c23"]), "thin_americas": andjoin(R["thin"]["americas_modelski"]),
     "london_rank2025_ord": ordn(L["un_rank2025"]), "london_rank1600_ord": ordn(L["rank1600"]), "london_rank1700_ord": ordn(L["rank1700"]), "london_rank1750_ord": ordn(L["rank1750"]),
     "lagos_r2025_ord": ordn(R["un"]["lagos"]["r2025"]), "lagos_r2050_ord": ordn(R["un"]["lagos"]["r2050"]),
     "jakarta_ch_rank_ord": ordn(R["seam_sum"]["jakarta_ch_rank"]), "jakarta_un_rank_ord": ordn(R["seam_sum"]["jakarta_un_rank"]),
     "ur2000_c": est(ur_i, "C", -2000)[0], "ur2000_m": est(ur_i, "M", -2000)[0], "tie700_n": len(snap(-700)["lead"]), "n_seam": len(seam),
     "phil": next(f["value"] for f in CHK["fixes"] if f["city"] == "Philadelphia")}
up = next(s for s in SNAPROWS if s["y"] > RG["Uruk"]["last"] and s["pop"] > RG["Uruk"]["peak"])
T["uruk_passed_y"] = up["y"]; T["uruk_passed_by"] = lead_name(up["y"]); T["uruk_passed_years"] = ydiff(RG["Uruk"]["last"], up["y"])
span = [s for s in SNAPROWS if 1100 <= s["y"] <= 1825]
T["china_n"] = sum(1 for s in span if all(creg(i) == 4 for i in s["lead"])); T["china_of"] = len(span)
eg = [s for s in SNAPROWS if -1600 <= s["y"] <= -1000]
T["egypt_n"] = sum(1 for s in eg if all(P.country[i] == "Egypt" for i in s["lead"])); T["egypt_of"] = len(eg)
lons = [c["lon"] for c in COG if 500 <= c["y"] <= 1825]; T["lon500_1825_min"] = min(lons); T["lon500_1825_max"] = max(lons)
T["meso_lon_min"] = min(c["lon"] for c in COG if c["y"] <= -800); T["meso_lon_max"] = max(c["lon"] for c in COG if c["y"] <= -800)
T["rome_c_share"] = round(100 * R["peak"]["rome"]["c_peak1000"] / R["peak"]["rome"]["m_peak"]); T["alex_c_share"] = round(100 * R["peak"]["alexandria"]["c_peak1000"] / R["peak"]["alexandria"]["m_peak"])
T["shrink1"], T["shrink2"] = R["un"]["shrinkers"][0]["name"], R["un"]["shrinkers"][1]["name"]
T["ny_un_rank_ord"] = ordn(R["seam_sum"]["ny_un_rank"])
for nm, key in (("Cahokia", "cahokia_n"), ("Zimbabwe", "zimbabwe_n")):
    T[key] = int((E.cid == P.index[P.name == nm][0]).sum())
m1900 = [i for i, p in zip(SR[1900]["top"], SR[1900]["toppop"]) if p >= 1e6] + [int(c) for c in SN[1900][SN[1900]["pop"] >= 1e6].cid if int(c) not in SR[1900]["top"]]
T["m1_1900_eu_na"] = sum(1 for i in m1900 if creg(i) in (2, 7)); assert len(m1900) == R["n"]["m1_1900"]
R["txt"] = T
R["method"] = {"gap1": CH_GAP[0][1], "gap2": CH_GAP[1][1], "gap3": CH_GAP[2][1], "gap_until1": CH_GAP[0][0], "gap_until2": CH_GAP[1][0], "match_km": 30, "link_km": 50,
               "mirror": 1300, "min_places": 8, "un_first": UN_FIRST, "un_last": UN_LAST, "un_step": 5, "un_map_min": 300000, "degurba_density": 1500, "degurba_min": 50000,
               "rise_n": 15, "top100": 100, "same_km": 5, "first_snap": SNAPS[0], "chandler_from": SNAP_CHANDLER[0], "chandler_to": SNAP_CHANDLER[-1]}

# ---------- data tables ----------
pd.DataFrame([{"place_id": i, "name": P.disp[i], "other_names": P.alt[i], "country": P.country[i], "lat": P.lat[i], "lon": P.lon[i], "region": RN[P.reg[i]],
               "certainty": P.cert[i], "sources": P.srcs[i].replace("C", "Chandler ").replace("M", "Modelski ").strip(),
               "un_city_code": int(U.City_Code[P.un[i]]) if P.un[i] >= 0 else ""} for i in P.index]).to_csv(f"{DATA}/places.csv", index=False)
E.assign(source=E.src.map({"C": "Chandler", "M": "Modelski"}))[["cid", "source", "year", "pop"]].rename(columns={"cid": "place_id", "pop": "population"}).to_csv(f"{DATA}/estimates.csv", index=False)
pd.DataFrame(CHK["fixes"]).to_csv(f"{DATA}/corrections.csv", index=False)
rows = []
for t in HIST:
    for r in SN[t].itertuples():
        rows.append((t, int(r.cid), P.disp[r.cid], round(r.pop), None if np.isnan(r.m) else round(r.m), None if np.isnan(r.c) else round(r.c), r.interp, "Chandler and Modelski"))
for t in SNAP_UN:
    for c, v in U[["City_Code", t]].dropna().itertuples(index=False):
        if v >= 3e5:
            rows.append((t, un2id[int(c)], cname(un2id[int(c)]), round(v), None, None, 0, "UN WUP 2025 (DEGURBA)"))
pd.DataFrame(rows, columns=["year", "place_id", "name", "population", "modelski", "chandler", "interpolated", "source"]).assign(name=lambda d: d.name.map(dash)).to_csv(f"{DATA}/snapshots.csv", index=False)
pd.DataFrame([{"year": s["y"], "source": {"M": "Modelski and Chandler", "C": "Chandler", "U": "UN WUP 2025"}[s["era"]] if s["y"] > -9999 else "",
               "largest": andjoin(cname(i, s["y"]) for i in s["lead"]), "population": round(s["pop"]), "second": cname(s["second"], s["y"]) if s["second"] is not None else "",
               "second_population": round(s["second_pop"]) if s["second_pop"] else "", "largest_modelski": andjoin(cname(i, s["y"]) for i in s.get("lead_m", [])),
               "largest_chandler": andjoin(cname(i, s["y"]) for i in s.get("lead_c", [])), "places": s["n"], "over_100k": s["n100k"], "over_1m": s["n1m"],
               "centre25_lat": c["lat"], "centre25_lon": c["lon"], "centre10_lat": c["lat10"], "centre10_lon": c["lon10"]} for s, c in zip(SNAPROWS, COG)]).to_csv(f"{DATA}/largest_city.csv", index=False)
pd.DataFrame([{"from": r["first"], "to": r["last"], "snapshots": r["n"], "largest": r["label"], "tie": r["tie"], "region": RN[r["reg"]], "peak_population": round(r["peak"])} for r in reigns]).to_csv(f"{DATA}/reigns.csv", index=False)
pd.DataFrame([{"year": r["y"], **{RN[k]: r["share"][k] for k in range(len(RN))}} for r in REGS]).to_csv(f"{DATA}/region_share_top25.csv", index=False)
g50s = U[U.City_Code.isin(rk[2050][:100])].sort_values(2050, ascending=False)
pd.DataFrame([{"rank_2050": k + 1, "city": r.short, "country": r.Location, "un_city_code": int(r.City_Code), "pop_1975": r[1975], "pop_2000": r[2000], "pop_2025": r[2025], "pop_2050": r[2050],
               "rank_2025": rk[2025].index(int(r.City_Code)) + 1, "plausibility": r.plaus} for k, (_, r) in enumerate(g50s.iterrows())]).rename(columns=lambda c: c).to_csv(f"{DATA}/un_largest_2050.csv", index=False)

# ---------- page data ----------
NC = NP + len(extra)
cities = []
for i in range(NC):
    if i < NP:
        p = P.loc[i]; j = int(p.un)
        lat, lon = cll(i)
        cities.append([p.disp, p.alt or "", p.country, round(float(p.lat), 3), round(float(p.lon), 3), int(p.reg), int(p.cert), p.srcs, j])
    else:
        j = UNROW[extra[i - NP]]; u = U.iloc[j]
        cities.append([u.short, u.City_Name if u.City_Name != u.short else "", u.Location, round(float(u.PWCent_Latitude), 3), round(float(u.PWCent_Longitude), 3), int(u.reg), 0, "U", j])
# UN series for the cities on the page, in thousands, every five years
useries = {}
for c in cities:
    j = c[8]
    if j >= 0 and j not in useries:
        u = U.iloc[j]
        useries[j] = [None if np.isnan(u[y]) else round(u[y] / 1000, 1) for y in SNAP_UN] + [round(float(u.PWCent_Latitude), 3), round(float(u.PWCent_Longitude), 3), u.plaus if isinstance(u.plaus, str) else "", u.short]
ukeys = sorted(useries); upos = {j: k for k, j in enumerate(ukeys)}
for c in cities:
    c[8] = upos.get(c[8], -1)
hist = [[[[int(y), int(v)] for y, v in zip(*ser[(i, "M")])] if (i, "M") in ser else [], [[int(y), int(v)] for y, v in zip(*ser[(i, "C")])] if (i, "C") in ser else []] for i in range(NP)]
snapdata = []
for s in SNAPROWS:
    t = s["y"]
    if t in SN:
        d = SN[t]; snapdata.append([[int(x) for x in d.cid], [round(v / 1000, 1) for v in d["pop"]], [int(x) for x in d.interp]])
    else:
        d = U[["City_Code", t]].dropna(); d = d[d.City_Code.astype(int).isin(show_un)].sort_values(t, ascending=False)
        d = d[d[t] >= 3e5]
        snapdata.append([[un2id[int(c)] for c in d.City_Code], [round(v / 1000, 1) for v in d[t]], []])
modern = U[U[2025] >= 1e6].sort_values(2025, ascending=False)
SITE = {"regions": REGIONS, "snaps": [s["y"] for s in SNAPROWS], "era": [s["era"] for s in SNAPROWS], "cities": cities, "hist": hist, "useries": [useries[j] for j in ukeys],
        "uyears": SNAP_UN, "snapdata": snapdata, "crown": [s["lead"] for s in SNAPROWS], "cog": [[c["lat"], c["lon"], c["lat10"], c["lon10"]] for c in COG],
        "modern": [[round(float(a), 2), round(float(b), 2), round(float(c) / 1000)] for a, b, c in zip(modern.PWCent_Latitude, modern.PWCent_Longitude, modern[2025])],
        "period": [[int(i), [[u, nm] for u, nm in PERIOD.get(P.name[i], [])]] for i in P.index if PERIOD.get(P.name[i])],
        "reigns": [{k: r[k] for k in ("first", "last", "n", "peak", "label", "tie", "reg", "ids")} for r in reigns], "np": NP}
jsave(SITE, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("reigns:", " | ".join(f"{r['label']} {r['first_t']}-{r['last_t']}" for r in reigns))
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB; cities", NC, "; disagreements", len(dis), "of", len(both))
