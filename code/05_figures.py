"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json and data/site.json."""
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
HALO = [pe.withStroke(linewidth=3.2, foreground=BG)]
SR = R["snaps"]; SN = SITE["snaps"]; CT = SITE["cities"]
lead_reg = [CT[SITE["crown"][k][0]][5] for k in range(len(SN))]


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def reign_strip(ax, y0, hgt):
    for r in SITE["reigns"]:
        k0, k1 = SN.index(r["first"]), SN.index(r["last"])
        x0 = (tpos(SN[k0 - 1]) + tpos(SN[k0])) / 2 if k0 else tpos(SN[0]); x1 = (tpos(SN[k1]) + tpos(SN[k1 + 1])) / 2 if k1 < len(SN) - 1 else tpos(SN[k1]) + 3
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, hgt, fc="#E8E4DA" if r["tie"] else RCOL[r["reg"]], ec="#C9C2B6" if r["tie"] else "none", lw=.5, transform=ax.get_xaxis_transform(), clip_on=False, zorder=3))


CROWN_LAB = [("Uruk", -2800, 0, 1.25, "center"), ("Memphis", -2000, 0, 1.55, "center"), ("Babylon", -600, 8, .62, "left"),
             ("Alexandria", -100, -6, 1.3, "right"), ("Rome", 200, -2, 1.35, "right"), ("Constantinople", 600, 0, .6, "center"), ("Chang'an", 700, 0, 1.45, "center"),
             ("Baghdad", 900, 6, 1.35, "left"), ("Hangzhou", 1300, 8, .7, "left"), ("Beijing", 1800, -6, 1.3, "right"), ("London", 1900, -6, 1.3, "right"),
             ("New York", 1950, 8, .78, "left"), ("Tokyo", 1975, -6, 1.3, "right"), ("Jakarta", 2025, 0, .72, "center"), ("Dhaka", 2050, -4, 1.3, "right")]


def crown_lines(ax, labels=CROWN_LAB, fs=9.5, src=True):
    x = tpos([s["y"] for s in SR]); y = [s["pop"] for s in SR]
    if src:
        for key, col, ls, lab in (("pop_m", GOLD, (0, (4, 3)), "Modelski's largest"), ("pop_c", COOL, (0, (1.5, 2)), "Chandler's largest")):
            q = [(tpos(s["y"]), s[key]) for s in SR if s["era"] != "U" and s.get(key)]
            ax.plot(*zip(*q), color=col, lw=1.3, ls=ls, label=lab, zorder=3)
    ax.plot(x, y, color=FG, lw=2, zorder=4, label="the largest (combined; UN from 1975)")
    ax.scatter(x, y, s=16, c=[RCOL[r] for r in lead_reg], ec=BG, lw=.4, zorder=5)
    ax.set_yscale("log"); ax.set_ylim(3e3, 9e7)
    ax.set_yticks([1e4, 1e5, 1e6, 1e7, 5e7]); ax.set_yticklabels(["10,000", "100,000", "1 million", "10 million", "50 million"], fontsize=9.5)
    ax.axvline(tpos(1975), color=MUT, lw=.8, ls=(0, (3, 3)), zorder=2)
    for n, yr, dx, f, ha in labels:
        s = next(q for q in SR if q["y"] == yr)
        ax.annotate(n, (tpos(yr), s["pop"]), xytext=(dx, 0), textcoords="offset points", ha=ha, va="center", fontsize=fs, fontweight="medium", path_effects=HALO, zorder=7) if False else \
            ax.text(tpos(yr) + dx * .6, s["pop"] * f, n, ha=ha, va="bottom" if f > 1 else "top", fontsize=fs, fontweight="medium", path_effects=HALO, zorder=7)
    ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True); spines(ax)


# ---------- the crown: size of the largest city ----------
fig = plt.figure(figsize=(12, 6.8), facecolor=BG); ax = fig.add_axes([.09, .25, .89, .65]); ax.set_facecolor(BG)
crown_lines(ax); time_axis(ax)
ax.tick_params(axis="x", pad=24)
reign_strip(ax, -.065, .05)
ax.text(tpos(1975) - 3, 6e7, "UN from 1975", ha="right", fontsize=9, color=MUT)
fig.text(.09, .955, "Population of the largest city at each snapshot (log scale); the band shows the region of the city on top", fontsize=11, color=FG)
fig.legend(handles=[Line2D([], [], color=FG, lw=2, label="the largest (combined; UN from 1975)"), Line2D([], [], color=GOLD, ls=(0, (4, 3)), label="Modelski's largest"),
                    Line2D([], [], color=COOL, ls=(0, (1.5, 2)), label="Chandler's largest")] + [Patch(color=c, label=n) for n, c in REGIONS],
           loc="lower center", ncol=4, frameon=False, fontsize=8.6, bbox_to_anchor=(.5, -.01), columnspacing=1.2, handlelength=1.6)
both(fig, "crown")

# ---------- the crown map ----------
fig = plt.figure(figsize=(12, 7.0), facecolor=BG); ax = fig.add_axes([0, .06, 1, .86])
pl, G = crown_map(fig, ax, R, SITE)
label_crowns(pl, G, size=8.6, sets=CROWN_SETS)
pl.check()
fig.text(.02, .955, "Every city that has been the world's largest, and the path of the centre of the 25 largest cities, 3700 BC to 2050", fontsize=11, color=FG)
import matplotlib.colors as mcolors
cax = fig.add_axes([.62, .05, .34, .018]); grad = np.linspace(0, 1, 256)[None, :]
cax.imshow(grad, aspect="auto", cmap=mcolors.ListedColormap([ERA_COL(v * .92) for v in np.linspace(0, 1, 256)]), extent=(0, 1000, 0, 1)); cax.set_yticks([])
cax.set_xticks(tpos([-3000, -1000, 1000, 1800, 2050])); cax.set_xticklabels(["3000 BC", "1000 BC", "1000", "1800", "2050"], fontsize=8); cax.set_title("path of the centre, by date", fontsize=8.5, loc="left", pad=3)
fig.legend(handles=[Patch(color=c, label=n) for n, c in REGIONS], loc="lower left", ncol=3, frameon=False, fontsize=8.2, bbox_to_anchor=(.01, -.005), columnspacing=.9)
both(fig, "map")

# ---------- regions of the 25 largest ----------
fig = plt.figure(figsize=(12, 5.4), facecolor=BG); ax = fig.add_axes([.07, .2, .91, .7]); ax.set_facecolor(BG)
x = tpos([r["y"] for r in R["regions"]]); sh = np.array([r["share"] for r in R["regions"]]).T
ax.stackplot(x, sh, colors=RCOL, lw=0, alpha=.93); ax.set_ylim(0, 100); time_axis(ax); spines(ax)
ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"]); ax.axvline(tpos(1975), color=BG, lw=1.2, ls=(0, (3, 3)))
fig.text(.07, .95, f"Share of the population of the {TOPN} largest places at each snapshot, by region", fontsize=11, color=FG)
fig.legend(handles=[Patch(color=c, label=n) for n, c in REGIONS], loc="lower center", ncol=5, frameon=False, fontsize=9, bbox_to_anchor=(.52, -.01))
both(fig, "regions")

# ---------- counts ----------
fig = plt.figure(figsize=(12, 5.2), facecolor=BG); ax = fig.add_axes([.08, .14, .9, .74]); ax.set_facecolor(BG)
D = R["counts"]
for key, col, lab in (("n100k", COOL, "100,000 or more"), ("n1m", HOT, "a million or more")):
    for seg in ([d for d in D if d["era"] != "U"], [d for d in D if d["era"] == "U"]):
        run = []
        for d in seg + [None]:
            if d is not None and d[key] > 0: run.append(d); continue
            if len(run) > 1: ax.plot(tpos([q["y"] for q in run]), [q[key] for q in run], color=col, lw=2)
            elif len(run) == 1: ax.plot(tpos([run[0]["y"]]), [run[0][key]], "o", color=col, ms=3)
            run = []
    ax.plot([], [], color=col, lw=2, label=lab)
ax.set_yscale("log"); ax.set_ylim(.7, 2e4); ax.set_yticks([1, 10, 100, 1000, 10000]); ax.set_yticklabels(["1", "10", "100", "1,000", "10,000"])
time_axis(ax); spines(ax); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True); ax.axvline(tpos(1975), color=MUT, lw=.8, ls=(0, (3, 3)))
n = R["n"]
for y, v, t in ((1900, n["m1_1900"], f"{n['m1_1900']} in 1900"), (2025, n["m1_2025"], f"{n['m1_2025']} in 2025")):
    ax.annotate(t, (tpos(y), v), xytext=(-8, 10), textcoords="offset points", ha="right", fontsize=9.5, color=HOT, path_effects=HALO)
ax.annotate(f"{n['k100_2025']:,} in 2025", (tpos(2025), n["k100_2025"]), xytext=(-14, 16), textcoords="offset points", ha="right", fontsize=9.5, color=COOL, path_effects=HALO)
ax.text(tpos(1975) - 4, 1.2e4, "before 1975: places in the compilations (floors)   |   UN cities", ha="right", fontsize=8.8, color=MUT)
ax.legend(loc="upper left", frameon=False, fontsize=9.5)
fig.text(.08, .945, "Places of 100,000 and of a million or more at each snapshot (log scale)", fontsize=11, color=FG)
both(fig, "counts")

# ---------- London and its rivals ----------
def track(name, ctry=None):
    i = next(j for j, c in enumerate(CT) if j < SITE["np"] and c[0] == name and (ctry is None or c[2] == ctry))
    out = []
    for k, y in enumerate(SN):
        d = SITE["snapdata"][k]
        if i in d[0] and y >= 1500:
            v = d[1][d[0].index(i)] * 1000
            if v >= 5e4: out.append((y, v, SITE["era"][k]))
    return out


fig = plt.figure(figsize=(12, 5.6), facecolor=BG); ax = fig.add_axes([.1, .1, .78, .79]); ax.set_facecolor(BG)
LT = [("London", "United Kingdom", HOT), ("Beijing", None, "#2E9A8C"), ("Istanbul", None, GOLD), ("Paris", None, "#7B57A8"), ("New York", None, NAVY), ("Tokyo", None, "#D46A8C")]
ends = []
for n_, c_, col in LT:
    t = track(n_, c_)
    for seg in ([p for p in t if p[2] != "U"], [p for p in t if p[2] == "U"]):
        if seg: ax.plot([p[0] for p in seg], [p[1] for p in seg], "-o", color=col, lw=3 if n_ == "London" else 1.6, ms=3.5 if n_ == "London" else 2.4)
    ends.append([t[-1][1], n_, col])
ends.sort(key=lambda e: e[0])
ly = [np.log10(e[0]) for e in ends]
for j in range(1, len(ly)): ly[j] = max(ly[j], ly[j - 1] + .1)
for (v, n_, col), l in zip(ends, ly): ax.text(2056, 10 ** l, n_, color=col, fontsize=10, va="center", fontweight="medium")
ax.set_yscale("log"); ax.set_ylim(5e4, 5e7); ax.set_xlim(1500, 2052); spines(ax); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.set_yticks([1e5, 1e6, 1e7]); ax.set_yticklabels(["100,000", "1 million", "10 million"]); ax.axvline(1975, color=MUT, lw=.8, ls=(0, (3, 3)))
L = R["london"]
ax.axvspan(L["cross_in"], L["cross_out"], color=HOT, alpha=.07, lw=0)
ax.text((L["cross_in"] + L["cross_out"]) / 2, 3.6e7, f"London the largest,\nabout {L['cross_in']} to {L['cross_out']}", ha="center", fontsize=9.5, color=HOT)
ax.text(1973, 6.5e4, "Chandler  |  UN", ha="center", fontsize=8.5, color=MUT)
fig.text(.08, .945, "London and its rivals, 1500 to 2050 (log scale): Chandler to 1970, the UN from 1975", fontsize=11, color=FG)
both(fig, "london")

# ---------- the 1975 seam ----------
S = R["seam"]
fig = plt.figure(figsize=(12, 5.8), facecolor=BG); ax = fig.add_axes([.17, .1, .78, .8]); ax.set_facecolor(BG)
yy = np.arange(len(S))[::-1]
ax.barh(yy + .18, [d["chandler1975"] / 1e6 for d in S], height=.34, color=COOL, label="Chandler 1975 (urban agglomeration)")
ax.barh(yy - .18, [(d["un1975"] or 0) / 1e6 for d in S], height=.34, color=HOT, label="UN 1975 (DEGURBA city)")
for y, d in zip(yy, S):
    ax.text(d["chandler1975"] / 1e6 + .2, y + .18, f"{d['chandler1975'] / 1e6:.1f}", va="center", fontsize=8.5, color=COOL)
    if d["un1975"]: ax.text(d["un1975"] / 1e6 + .2, y - .18, f"{d['un1975'] / 1e6:.1f}  (UN rank {d['un_rank1975']})", va="center", fontsize=8.5, color=HOT)
ax.set_xlim(0, 29.5); ax.set_yticks(yy); ax.set_yticklabels([d["name"] for d in S], fontsize=10); ax.set_xlabel("million people"); spines(ax); ax.tick_params(axis="y", length=0)
ax.legend(loc="lower right", frameon=False, fontsize=9.5)
fig.text(.17, .945, f"Chandler's {len(S)} largest places in 1975, and the UN's figure for the same city that year", fontsize=11, color=FG)
both(fig, "seam")

# ---------- 2050 ----------
D = R["un"]["top2050_25"][:15]
fig = plt.figure(figsize=(12, 6.2), facecolor=BG); ax = fig.add_axes([.17, .11, .78, .79]); ax.set_facecolor(BG)
yy = np.arange(len(D))[::-1]
for y, d in zip(yy, D):
    c = RCOL[d["reg"]]; ax.plot([d["p2025"] / 1e6, d["p2050"] / 1e6], [y, y], color=c, lw=3, alpha=.5)
    ax.scatter([d["p2025"] / 1e6], [y], s=60, facecolor=BG, edgecolor=c, lw=2, zorder=3); ax.scatter([d["p2050"] / 1e6], [y], s=70, color=c, zorder=3)
    ax.text(max(d["p2025"], d["p2050"]) / 1e6 + .9, y, f"{d['p2050'] / 1e6:.1f}m", va="center", fontsize=9)
ax.set_yticks(yy); ax.set_yticklabels([f"{k + 1}. {d['name']}" for k, d in enumerate(D)], fontsize=10); ax.set_xlim(0, 58); spines(ax); ax.tick_params(axis="y", length=0)
ax.set_xlabel("million people"); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
ax.legend(handles=[Line2D([], [], ls="", marker="o", mfc=BG, mec=FG, label="2025"), Line2D([], [], ls="", marker="o", mfc=FG, mec=FG, label="2050 (projection)")],
          loc="lower right", frameon=False, fontsize=9.5)
fig.text(.17, .945, "The 15 largest cities of 2050 in the UN's projection, against 2025 (colour: region)", fontsize=11, color=FG)
both(fig, "2050")

# ---------- centre of gravity longitude (paper only) ----------
fig = plt.figure(figsize=(12, 4.6), facecolor=BG); ax = fig.add_axes([.08, .14, .9, .74]); ax.set_facecolor(BG)
cg = R["cog"]; x = tpos([c["y"] for c in cg])
ax.plot(x, [c["lon10"] for c in cg], color=MUT, lw=1, label="10 largest"); ax.plot(x, [c["lon"] for c in cg], color=FG, lw=2.2, label=f"{TOPN} largest")
for v, t in ((45, "Baghdad 45°E"), (116, "Beijing 116°E"), (0, "London 0°")): ax.axhline(v, color=RULE, lw=.8, zorder=0); ax.text(1000, v + 3, t, ha="right", fontsize=8.5, color=MUT)
ax.set_ylim(-80, 140); time_axis(ax); spines(ax); ax.set_ylabel("longitude (°E)"); ax.legend(loc="lower left", frameon=False, fontsize=9.5); ax.axvline(tpos(1975), color=MUT, lw=.8, ls=(0, (3, 3)))
both(fig, "cog", blog=False)

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.36, .27, .64, .7])
pl, G = crown_map(fig, ax, R, SITE, labels=False, size=.7)
a2 = fig.add_axes([.42, .07, .55, .17]); a2.set_facecolor(BG)
crown_lines(a2, labels=[("Uruk", -2800, 0, 1.4, "center"), ("Rome", 200, -2, 1.4, "right"), ("Beijing", 1800, -6, 1.4, "right"), ("London", 1900, -6, 1.4, "right"), ("Dhaka", 2050, -4, 1.4, "right")], fs=8, src=False)
a2.set_yticks([]); a2.spines["left"].set_visible(False); a2.set_xticks(tpos([-3000, 1, 1800, 2050])); a2.set_xticklabels(["3000 BC", "AD 1", "1800", "2050"], fontsize=8); a2.set_xlim(0, 1000); a2.minorticks_off()
fig.text(.04, .88, "The largest", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .74, "city", fontproperties=DISP, fontsize=50, color=HOT, va="top")
fig.text(.04, .60, "on Earth", fontproperties=DISP, fontsize=50, color=GOLD, va="top")
fig.text(.04, .41, f"Six thousand years of the world's\nbiggest cities, from Uruk to Dhaka,\nand the path of the urban world's centre.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.35)
fig.text(.04, .04, "maps.tristanhotham.com/largest-cities", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
