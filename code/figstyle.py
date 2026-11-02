"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines in the Equal Earth projection, the stretched time axis used in
every chart, and the crown map (crown cities, the centre of gravity path, labels placed on open sea or paper)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1D2128", "#5F666E", "#E4DFD3", "#DDD8CC", "#EEF1F2"
HOT, GOLD, COOL, NAVY = "#B8352B", "#C99012", "#2F5FA7", "#1F2F4D"
RCOL = [c for _, c in REGIONS]; RN = [r for r, _ in REGIONS]

EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


MIN_ISLAND = 3e9    # m2: islands smaller than about 3,000 km2 are left off the static maps (world-scale generalisation)
SHAPES = []
for f in W["features"]:
    for ring in rings(f["geometry"]):
        x, y = EE.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
        if abs(0.5 * np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])) < MIN_ISLAND: continue
        SHAPES.append((f["properties"]["iso"], np.column_stack([x, y]), ring))
WORLD_EXT = (-17.0e6, 17.0e6, -6.6e6, 8.7e6)


def world(ax, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1):
    for iso, p, _ in SHAPES:
        ax.add_patch(MPoly(p, closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    """Equal Earth globe outline."""
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, -180), lat); xr, yr = EE.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def proj(lon, lat):
    return EE.transform(np.asarray(lon), np.asarray(lat))


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---------- the stretched time axis (same knots as the page) ----------
KN = [(0, -3700), (220, -1000), (340, 1), (500, 1000), (620, 1500), (740, 1800), (800, 1900), (860, 1975), (1000, 2050)]


def tpos(y):
    y = np.asarray(y, float)
    return np.interp(y, [k[1] for k in KN], [k[0] for k in KN])


TICKS = [-3000, -2000, -1000, 1, 1000, 1500, 1800, 1900, 1975, 2050]
tlab = lambda y: f"{-y} BC" if y < 0 else ("AD 1" if y == 1 else str(y))


def time_axis(ax, ticks=TICKS, size=10):
    ax.set_xlim(0, 1000); ax.set_xticks(tpos(ticks)); ax.set_xticklabels([tlab(t) for t in ticks], fontsize=size)


# ---------- the crown map ----------
from shapely.geometry import shape as _shape, box as _box, Point as _Pt, LineString as _LS, Polygon as _Poly
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep as _prep
_land = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = _shape(f["geometry"]); gs = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for q in gs:
        xy = np.array(q.exterior.coords); x, y = EE.transform(np.clip(xy[:, 0], -179.99, 179.99), np.clip(xy[:, 1], -89.9, 89.9))
        pg = _Poly(np.column_stack([x, y])).buffer(0)
        if pg.area >= MIN_ISLAND: _land.append(pg)
LANDU = unary_union(_land)


def crown_groups(R, SITE):
    """The crown cities, one marker each (first reign's place), grouped for labelling."""
    C = SITE["cities"]; seen = {}
    for r in R["reigns"]:
        if r["tie"]: continue
        i = r["ids"][0]
        if i not in seen:
            seen[i] = {"id": i, "name": r["label"], "lat": C[i][3], "lon": C[i][4], "reg": C[i][5], "runs": [], "peak": 0}
        seen[i]["runs"].append((r["first"], r["last"])); seen[i]["peak"] = max(seen[i]["peak"], r["peak"])
        if r["label"] != seen[i]["name"] and r["label"] not in seen[i]["name"]:
            seen[i]["name"] += " (" + r["label"] + ")"
    return list(seen.values())


def span_txt(runs):
    out = []
    for a, b in runs:
        if a == b: out.append(yfmt(a, True))
        elif b < 0: out.append(f"{-a} to {-b} BC")
        elif a < 0: out.append(f"{-a} BC to AD {b}")
        elif a < 1000: out.append(f"AD {a} to {b}")
        else: out.append(f"{a} to {b}")
    return ", ".join(out)


class Placer:
    """Labels placed on open sea (or the paper around the globe): a label's box must stay LAND_MARGIN away from land,
    must not touch a marker, the path or another label; a leader, where needed, must not cross another label."""

    def __init__(self, fig, ax, margin=30e3, halo=None, strict=True):
        self.fig, self.ax, self.strict = fig, ax, strict
        self.land = _prep(LANDU.buffer(margin)); self.obst = []; self.placed = []; self.lines = []
        self.halo = halo or [pe.withStroke(linewidth=3.5, foreground=SEA)]
        fig.canvas.draw(); self.ren = fig.canvas.get_renderer()

    def obstacle(self, geom):
        self.obst.append(geom)

    def tbox(self, t):
        bb = t.get_window_extent(self.ren)
        (x0, y0), (x1, y1) = self.ax.transData.inverted().transform([[bb.x0 - 4, bb.y0 - 3], [bb.x1 + 4, bb.y1 + 3]])
        return _box(x0, y0, x1, y1)

    def bad(self, b):
        x0, x1 = self.ax.get_xlim(); y0, y1 = self.ax.get_ylim()
        if not _box(x0 + 1e5, y0 + 1e5, x1 - 1e5, y1 - 1e5).contains(b): return True
        if self.strict and self.land.intersects(b): return True
        return any(b.intersects(o) for o in self.obst) or any(b.intersects(o) for _, _, o in self.placed) or any(b.intersects(l) for _, l in self.lines)

    def place(self, name, s, lonlat, target=None, ha="center", col=FG, size=10, w="medium", lead_gap=2.5e5, maxr=40, step=1.0, font=None):
        kw = {"fontproperties": font} if font is not None else {"family": MONO, "fontweight": w}
        t = self.ax.text(0, 0, s, ha=ha, va="center", fontsize=size, color=col, linespacing=1.18, zorder=12, path_effects=self.halo, **kw)
        if font is not None: t.set_fontsize(size)
        lon0, lat0 = lonlat
        cands = [(lon0 + dx * step, lat0 + dy * step) for r in range(0, maxr + 1) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
        for lon, lat in cands:
            if abs(lat) > 84 or abs(lon) > 180: continue
            x, y = proj(lon, lat); t.set_position((float(x), float(y))); b = self.tbox(t)
            if self.bad(b): continue
            ln = None
            if target is not None:
                tx, ty = proj(target[0], target[1]); c = _Pt(float(tx), float(ty)); gap = b.distance(c) - target[2]
                if gap > lead_gap:
                    pb, _ = nearest_points(b, c); d = np.hypot(pb.x - c.x, pb.y - c.y)
                    e = (c.x + (pb.x - c.x) * target[2] / d, c.y + (pb.y - c.y) * target[2] / d)
                    ln = _LS([(pb.x, pb.y), e])
                    if any(ln.intersects(o) for _, _, o in self.placed): continue
            self.placed.append((name, t, b))
            if ln is not None:
                self.lines.append((name, ln)); self.ax.plot(*ln.xy, color=FG, lw=.7, zorder=11)
            return t
        raise RuntimeError("no clean spot for " + name)

    def check(self):
        for nm, t, b in self.placed:
            if self.strict: assert not self.land.intersects(b), nm
            assert not any(b.intersects(o) for n2, _, o in self.placed if n2 != nm), nm
        for nm, l in self.lines:
            assert not any(l.intersects(o) for n2, _, o in self.placed if n2 != nm), nm


ERA_COL = plt.get_cmap("viridis")


def era_col(y):
    return ERA_COL(float(tpos(y)) / 1000 * .92)


def crown_map(fig, ax, R, SITE, strict=True, size=1.0, labels=True, sea=SEA, land=LAND, halo_col=None):
    """Crown cities (markers coloured by region, ringed) and the centre of gravity path of the 25 largest, coloured by
    date. Returns the Placer so callers can check or add labels."""
    outline(ax, fc=sea, ec="#C9CDD0", lw=.8); world(ax, lw=.25, land=land, ec=sea)
    cg = R["cog"]; xs, ys = proj([c["lon"] for c in cg], [c["lat"] for c in cg])
    for k in range(len(cg) - 1):
        ax.plot(xs[k:k + 2], ys[k:k + 2], color=era_col(cg[k]["y"]), lw=2.2 * size, zorder=5, solid_capstyle="round")
    ax.scatter(xs, ys, s=7 * size, c=[era_col(c["y"]) for c in cg], zorder=6, lw=0)
    G = crown_groups(R, SITE)
    pl = Placer(fig, ax, halo=[pe.withStroke(linewidth=3.5, foreground=halo_col or sea)], strict=strict)
    for g in G:
        x, y = proj(g["lon"], g["lat"]); g["xy"] = (float(x), float(y))
        ax.scatter([x], [y], s=46 * size, c=RCOL[g["reg"]], ec="#FFFFFF", lw=1.1, zorder=8)
        pl.obstacle(_Pt(x, y).buffer(1.1e5))
    for c in cg:   # the path as an obstacle
        pass
    pl.obstacle(_LS(list(zip(xs, ys))).buffer(6e4))
    if not labels: return pl, G
    return pl, G


def label_crowns(pl, G, size=9.5, sets=None, dates=False):
    """Grouped labels for the crown cities, placed on sea with leaders where needed."""
    by = {g["name"]: g for g in G}
    def tgt(names):
        pts = np.array([by[n]["xy"] for n in names]); c = pts.mean(0)
        r = max(1.3e5, float(np.max(np.hypot(*(pts - c).T))) + 1.2e5)
        lon, lat = EE.transform(c[0], c[1], direction="INVERSE"); return (float(lon), float(lat), r)
    for key, names, title, pref, ha in sets:
        names = [n for n in names if n in by]
        if not names: continue
        if dates:
            body = "\n".join(f"{n} {span_txt(by[n]['runs'])}" for n in names)
        else:   # names only, wrapped to about 24 characters a line
            lines, cur = [], ""
            for n in names:
                add = (", " if cur else "") + n
                if cur and len(cur + add) > 24: lines.append(cur + ","); cur = n
                else: cur += add
            body = "\n".join(lines + [cur])
        s = (title + "\n" + body) if title else body
        pl.place(key, s, pref, target=tgt(names), ha=ha, size=size, lead_gap=2.0e5, maxr=70)
    pl.check()


CROWN_SETS = [
    ("babylon", ["Babylon", "Nineveh", "Ctesiphon", "Baghdad", "Merv"], "MESOPOTAMIA AND PERSIA", (68, -18), "left"),
    ("sumer", ["Eridu", "Uruk", "Lagash", "Mari", "Girsu", "Ur"], "SUMER", (60, 14), "left"),
    ("egypt", ["Memphis", "Avaris", "Thebes", "Pi-Ramesses", "Alexandria"], "EGYPT", (25, 12), "right"),
    ("med", ["Rome", "Constantinople (Istanbul)"], "", (-14, 38), "right"),
    ("china", ["Yin", "Linzi", "Chang'an", "Kaifeng", "Hangzhou", "Nanjing", "Beijing"], "CHINA", (138, 30), "left"),
    ("london", ["London"], "", (-22, 52), "right"),
    ("ny", ["New York"], "", (-55, 36), "left"),
    ("tokyo", ["Tokyo"], "", (152, 42), "left"),
    ("jakarta", ["Jakarta"], "", (100, -14), "center"),
    ("dhaka", ["Dhaka"], "", (88, 14), "center"),
]
