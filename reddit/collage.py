"""r/dataisbeautiful collage for largest-cities: 2400 x 3200 px, light background. Numbers from data/results.json.
Map labels sit on open sea or on the paper around the globe, with a halo; where a leader is needed it never crosses
another label (checked by figstyle.Placer)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
BGc = "#F7F5F0"; SEAc = "#E9EFF2"; LANDc = "#E2DDD1"
HALOP = [pe.withStroke(linewidth=4, foreground=BGc)]
un, L, s, RG = R["un"], R["london"], R["source"], R["reign"]
SN = SITE["snaps"]

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "The largest city on Earth", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, .941, f"{R['n_crown_sole']} cities have been the world's largest in 6,000 years: from Uruk, {round(RG['Uruk']['peak']):,} people in 2800 BC, to Jakarta,\n"
         f"{un['jakarta2025'] / 1e6:.1f} million in 2025. The line follows the centre of the {TOPN} largest cities, from Mesopotamia to Tibet.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.45)

# ---- map
ax = fig.add_axes([0, .515, 1, .37])
pl, G = crown_map(fig, ax, R, SITE, sea=SEAc, land=LANDc, size=1.25)
label_crowns(pl, G, size=9.6, sets=CROWN_SETS)
pl.check()
print("labels ok:", len(pl.placed), "leaders:", [n for n, _ in pl.lines])

# ---- legend under the map
LP = SERP.copy(); LP.set_size(11)
fig.text(.045, .512, "Dots: every city that has been the world's largest on its own (colour: region). Line: the population-weighted centre of the 25 largest\n"
         "cities at each of 85 snapshots, coloured by date. A centre of cities spread round the globe falls far to the north, as in 1850 to 1970.",
         fontsize=9.4, color=MUT, va="top", linespacing=1.45)
fig.legend(handles=[Line2D([], [], ls="", marker="o", ms=10, mfc=c, mec="#fff", label=n) for n, c in REGIONS],
           loc="upper left", bbox_to_anchor=(.035, .488), ncol=2, frameon=False, prop=LP, handletextpad=.3, columnspacing=1.2, labelspacing=.5)
cax = fig.add_axes([.62, .452, .33, .012])
cax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=mcolors.ListedColormap([ERA_COL(v * .92) for v in np.linspace(0, 1, 256)]), extent=(0, 1000, 0, 1))
cax.set_yticks([]); cax.set_xticks(tpos([-3000, -1000, 1000, 1800, 2050])); cax.set_xticklabels(["3000 BC", "1000 BC", "1000", "1800", "2050"], fontsize=8.5)
cax.set_title("path of the centre, by date", fontsize=9.5, loc="left", pad=4, color=FG)
assert s["n_snaps"] == 85 and R["cog_sum"]["west"]["lat"] > 60

# ---- numbers row
nums = [(f"{R['n_crown_sole']}", GOLD, "cities have been the\nworld's largest"),
        (f"{R['txt']['china_n']} of {R['txt']['china_of']}", "#2E9A8C", "snapshots 1100 to 1825 with\na Chinese city on top"),
        (f"~{L['years_est']} yrs", HOT, f"London on top, about\n{L['cross_in']} to {L['cross_out']}"),
        (f"{un['dhaka2050'] / 1e6:.1f}m", "#7B57A8", f"Dhaka in {un['dhaka_first'] + 1}, just ahead\nof Jakarta (UN projection)")]
for i, (big, col, small) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, .395, big, fontproperties=DISP, fontsize=33, color=col, va="top")
    fig.text(xx, .358, small, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.4)
assert un["dhaka_first"] + 1 == 2050

# ---- the crown through time
a = fig.add_axes([.1, .168, .86, .128]); a.set_facecolor(BGc)
SR = R["snaps"]; lead_reg = [SITE["cities"][SITE["crown"][k][0]][5] for k in range(len(SN))]
x = tpos([q["y"] for q in SR]); y = [q["pop"] for q in SR]
a.plot(x, y, color=FG, lw=2, zorder=4); a.scatter(x, y, s=16, c=[RCOL[r] for r in lead_reg], ec=BGc, lw=.4, zorder=5)
a.set_yscale("log"); a.set_ylim(3e3, 1.2e8); a.set_yticks([1e4, 1e5, 1e6, 1e7]); a.set_yticklabels(["10,000", "100,000", "1 million", "10 million"], fontsize=9.5)
a.axvline(tpos(1975), color=MUT, lw=.8, ls=(0, (3, 3))); a.grid(axis="y", color=RULE, lw=.8); a.set_axisbelow(True); spines(a)
time_axis(a, size=9.5); a.tick_params(axis="x", pad=24); a.minorticks_off()
for r in SITE["reigns"]:
    k0, k1 = SN.index(r["first"]), SN.index(r["last"])
    x0 = (tpos(SN[k0 - 1]) + tpos(SN[k0])) / 2 if k0 else tpos(SN[0]); x1 = (tpos(SN[k1]) + tpos(SN[k1 + 1])) / 2 if k1 < len(SN) - 1 else tpos(SN[k1]) + 3
    a.add_patch(plt.Rectangle((x0, -.1), x1 - x0, .08, fc="#E8E4DA" if r["tie"] else RCOL[r["reg"]], ec="none", transform=a.get_xaxis_transform(), clip_on=False))
a.set_title("How big the biggest city was (log scale), and where it was (band)", family=MONO, fontsize=13, color=FG, loc="left", pad=10)
for n_, yr, dx, f, ha in (("Uruk", -2800, 0, 1.5, "center"), ("Babylon", -600, 6, .55, "left"), ("Rome", 200, -2, 1.6, "right"), ("Chang'an", 700, 0, 1.6, "center"),
                          ("Baghdad", 900, 10, 1.3, "left"), ("Hangzhou", 1300, 4, .55, "left"), ("Beijing", 1800, -6, 1.6, "right"), ("London", 1900, -6, 1.5, "right"),
                          ("Tokyo", 1975, -8, 1.4, "right"), ("Jakarta", 2025, 0, .62, "center"), ("Dhaka", 2050, -4, 1.4, "right")):
    q = next(z for z in SR if z["y"] == yr)
    a.text(tpos(yr) + dx * .6, q["pop"] * f, n_, ha=ha, va="bottom" if f > 1 else "top", fontsize=9.5, fontweight="medium", path_effects=HALOP, zorder=7)
a.text(tpos(1975) + 4, 5e3, "UN from 1975", ha="left", fontsize=9, color=MUT)

# ---- small panels: the 2050 top five, and London
b3 = fig.add_axes([.1, .05, .38, .046]); b3.axis("off")
b3.set_title("Largest cities in 2050 (UN projection)", family=MONO, fontsize=11, color=FG, loc="left", pad=6)
T5 = un["top2050"][:5]
for i, d in enumerate(T5):
    yy = .9 - i * .21; w = .55 * d["pop"] / T5[0]["pop"]
    b3.text(0, yy, d["name"], fontsize=10, color=FG, va="center", transform=b3.transAxes)
    b3.barh([yy], [w], left=.3, height=.13, color=RCOL[d["reg"]], transform=b3.transAxes)
    b3.text(.32 + w, yy, f"{d['pop'] / 1e6:.1f}m", fontsize=9.5, va="center", transform=b3.transAxes)
b4 = fig.add_axes([.58, .05, .37, .046]); b4.axis("off")
b4.set_title("When the biggest city passed...", family=MONO, fontsize=11, color=FG, loc="left", pad=6)
sz = R["size"]
for i, (thr, k) in enumerate((("100,000", "first_100k"), ("1 million", "first_1m"), ("10 million", "first_10m"), ("20 million", "first_20m"))):
    d = sz[k]; b4.text(0, .9 - i * .25, f"{thr:>10}  {yfmt(d['y'], True):>8}  {d['city']}", fontsize=10, family=MONO, color=FG, va="center", transform=b4.transAxes)

fig.text(.045, .006, "Source: Reba, Reitsma and Seto (2016), Scientific Data 3:160034, from Chandler (1987) and Modelski (2003), CC BY 4.0; UN World Urbanization Prospects 2025\n"
         "(CC BY 3.0 IGO), cities by the Degree of Urbanisation, from 1975. Estimates before 1950 are uncertain; where the two compilations differ, their average is used.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/largest-cities", family=MONO, fontsize=8.3, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "largest_city_on_earth.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
