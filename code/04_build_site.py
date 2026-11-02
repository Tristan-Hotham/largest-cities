"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; the page data (results, site.json, world.json) is embedded. Facts stated in words (dates of reigns,
places, orderings) are checked here. The full-screen snippet (code/fullscreen_snippet.html) is pasted before </body>.
10.5281/zenodo.23872999, https://doi.org/10.5281/zenodo.23872999 and https://blog.tristanhotham.com/2026/10/31/largest-cities/ stay as placeholders for the publisher."""
import json
from common import *

KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
RG, S, T, U, L, CG = R["reign"], R["S"], R["txt"], R["un"], R["london"], R["cog_sum"]
runs = [(r["label"], r["first"], r["last"]) for r in R["reigns"]]

# facts stated in words (page, blog, paper, collage)
assert S["-3700"]["n"] == 1 and S["-3700"]["lead"] == ["Eridu"]
assert RG["Uruk"]["first"] == -3500 and RG["Uruk"]["last"] == -2800 and RG["Uruk"]["n_runs"] == 1
order = [l for l, a, b in runs]
assert order[2:6] == ["Lagash", "Mari", "Girsu", "Ur"]                                   # "Lagash, Mari and Girsu, to Ur"
assert ("Memphis", -2000, -2000) in runs and ("Babylon", -1700, -1700) in runs and ("Yin", -1300, -1300) in runs
assert {l for l, a, b in runs if -1600 <= a <= -1000} - {"Yin"} == {"Avaris", "Thebes", "Pi-Ramesses"}
assert ("Babylon, Memphis and Thebes", -900, -800) in runs and S["-700"]["lead"].__len__() == T["tie700_n"]
assert [(a, b) for l, a, b in runs if l == "Linzi"] == [(-500, -500), (-300, -300)] and ("Alexandria", -200, -100) in runs
assert ("Rome", 1, 400) in runs and ("Constantinople", 500, 600) in runs and ("Ctesiphon", 622, 622) in runs and ("Chang'an", 700, 700) in runs
assert ("Baghdad and Chang'an", 800, 800) in runs and ("Baghdad", 900, 1000) in runs
assert ("Kaifeng", 1100, 1100) in runs and ("Merv", 1150, 1150) in runs and ("Hangzhou", 1200, 1350) in runs and ("Nanjing", 1400, 1400) in runs
assert ("Beijing", 1450, 1600) in runs and ("Istanbul", 1650, 1700) in runs and ("Beijing", 1750, 1825) in runs
assert ("London", 1850, 1914) in runs and ("London and New York", 1925, 1925) in runs and ("New York", 1950, 1950) in runs
assert ("Tokyo", 1970, 2005) in runs and ("Jakarta and Tokyo", 2010, 2010) in runs and ("Jakarta", 2015, 2045) in runs and ("Dhaka", 2050, 2050) in runs
assert S["1300"]["lead"] == ["Hangzhou"] and S["1700"]["lead"] == ["Istanbul"] and S["1100"]["lead"] == ["Kaifeng"]
assert R["size"]["first_1m_m"]["city"] == "Alexandria" and R["peak"]["alexandria"]["m_peak"] == 1e6 and R["size"]["first_1m_c"]["city"] == "Beijing"
assert R["size"]["first_100k_c"]["city"] == "Avaris" and R["size"]["first_10m"]["city"] == "New York" and R["size"]["first_10m"]["y"] == 1950
assert R["size"]["first_20m"]["city"] == "Tokyo" and R["size"]["first_20m"]["y"] == 1970 and R["size"]["first_20m"]["era"] == "C"
assert S["1900"]["lead"] == ["London"] and S["1800"]["lead"] == ["Beijing"] and R["n"]["m1_1800"] == 1
assert T["uruk_passed_by"] == "Ur" and T["china_n"] > T["china_of"] / 2 and T["egypt_n"] == T["egypt_of"] - 1
# the centre of gravity, described in words
assert 30 < T["meso_lon_min"] and T["meso_lon_max"] < 52                                  # "from the Nile to the edge of Iran"
assert 55 < CG["c1500"]["lon"] < 85 and 58 < CG["c1900"]["lat"] < 62 and -8 < CG["c1900"]["lon"] < 0      # "north of Scotland"
assert 63 < CG["west"]["lat"] < 70 and -35 < CG["west"]["lon"] < -15                      # "between Iceland and Greenland"
assert 28 < CG["c2025"]["lat"] < 33 and 90 < CG["c2025"]["lon"] < 98                     # "eastern Tibet"
assert 26.5 < CG["c2050"]["lat"] < 28.5 and 85 < CG["c2050"]["lon"] < 88.3               # "eastern Nepal"
assert CG["c_m500"]["lon"] > CG["c_m3000"]["lon"] + 20 and CG["c100"]["lon"] < CG["c_m500"]["lon"] - 20   # east, then back west with Rome
assert R["reg_sum"]["eu_2025_n"] == 1                                                     # "and 1 is in Europe"
# London
assert L["rank1800"] == 2 and S["1800"]["lead"] == ["Beijing"] and L["p1850"] > 1.3 * L["bj1850"] and L["ny1950"] > 1.3 * L["p1950"]   # "clearly", "well ahead"
assert L["gap1825_pct"] < 2 and L["gap1925_pct"] < 1
# compilations, definitions and 2050
assert R["baghdad1000"]["c_lead"] == "Cordoba" and T["rome_c_share"] < 50 and T["alex_c_share"] < 50
assert abs(R["seam_sum"]["tokyo_un"] / R["seam_sum"]["tokyo_ch"] - 1) < .1 and R["seam_sum"]["ny_un"] < R["seam_sum"]["ny_ch"]          # "close enough"; American smaller
assert R["seam_sum"]["jakarta_un"] > 2 * R["seam_sum"]["jakarta_ch"]
assert U["hajipur"]["p2025"] > 5e6 and U["dhaka_margin_2050_pct"] < 2
assert [g["name"] for g in U["gainers"][:5]] == ["Dhaka", "Karachi", "Jakarta", "Luanda", "Cairo"] and U["new_top10_2050"] == ["Karachi"]
assert [g["name"] for g in U["fastest10m"][:3]] == ["Luanda", "Dar es Salaam", "Addis Ababa"]
assert U["tokyo2050"] < U["tokyo2025"] and U["jakarta_first"] == 2010
assert any(f["city"] == "Teotihuacan" and f["year"] == -900 for f in R["fixes"]) and any(f["city"] == "Philadelphia" for f in R["fixes"])
assert any("Košice" in n for n in R["cp1252_names"]) and any("Šomron" in n for n in R["cp1252_names"])
assert set(SNAPS) >= {-1360, -650, -430, 361, 622} and R["method"]["chandler_from"] == 1100 and R["method"]["chandler_to"] == 1970
# the jump buttons on the map land on a reign of that city
for nm, y in (("Uruk", -2800), ("Memphis", -2000), ("Babylon", -600), ("Alexandria", -100), ("Rome", 200), ("Constantinople", 600), ("Chang'an", 700), ("Baghdad", 900),
              ("Kaifeng", 1100), ("Hangzhou", 1300), ("Beijing", 1800), ("London", 1900), ("New York", 1950), ("Tokyo", 1975), ("Jakarta", 2025), ("Dhaka", 2050)):
    assert S[str(y)]["lead"] == [nm.replace("Constantinople", "Constantinople")] or (nm == "Constantinople" and S[str(y)]["lead"] == ["Constantinople"]), (nm, y, S[str(y)]["lead"])


def fill(tpl):
    out = re.sub(r"\{\{(?!(?:DOI|DOI_URL|BLOG_URL)\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = set(re.findall(r"\{\{([^}]*)\}\}", out))
    assert left <= KEEP, left
    return out


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl)
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    page_R = {k: R[k] for k in ("snaps", "counts", "regions", "cog", "disagree", "seam", "coverage", "eras", "fixes", "source", "un")}
    html = html.replace("/*RESULTS*/", J(page_R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
