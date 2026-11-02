"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23872999, https://doi.org/10.5281/zenodo.23872999 and https://blog.tristanhotham.com/2026/10/31/largest-cities/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Largest_City"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# the page build checks the shared facts; these are numbers written in words or in alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
un, S = R["un"], R["S"]
assert round(S["-3700"]["pop"], -3) == 6000 and R["reign"]["Uruk"]["peak"] == 80000                                      # "about 6,000 to 80,000"
assert [round(d["p2025"] / 1e5) / 10 for d in un["top2050_25"][:2]] == [36.6, 41.9] and round(un["dhaka2050"] / 1e5) / 10 == 52.1 and round(un["jakarta2050"] / 1e5) / 10 == 51.8
k = {d["name"]: d for d in un["top2050_25"]}
assert (round(k["Karachi"]["p2025"] / 1e5) / 10, round(k["Karachi"]["p2050"] / 1e5) / 10) == (21.4, 32.6) and round(k["Tokyo"]["p2050"] / 1e5) / 10 == 30.7
assert (round(k["Luanda"]["p2025"] / 1e5) / 10, round(k["Luanda"]["p2050"] / 1e5) / 10) == (11.4, 20.3) and [d["name"] for d in un["top2050_25"][:15]][-1] == "Luanda"
assert k["Seoul"]["p2050"] < k["Seoul"]["p2025"]
sm = {d["name"]: d for d in R["seam"]}
assert round(sm["New York"]["chandler1975"] / 1e5) / 10 == 17.1 and round(sm["New York"]["un1975"] / 1e5) / 10 == 12.1 and len(R["seam"]) == 12
assert all(sm[c]["un1975"] < sm[c]["chandler1975"] for c in ("Moscow", "London", "Paris", "Rio de Janeiro")) and all(sm[c]["un1975"] > sm[c]["chandler1975"] for c in ("São Paulo", "Buenos Aires"))
assert R["n"]["m1_1900"] == 16 and R["n"]["m1_2025"] == 511 and R["n"]["k100_2025"] == 6172 and R["n"]["m1_1800"] == 1
assert 1820 <= R["london"]["cross_in"] <= 1829 and 1920 <= R["london"]["cross_out"] <= 1929                                 # "in the 1820s", "in the 1920s"
assert R["reg_sum"]["eu_1900"] > 50                                                                                       # "more than half by 1900"
assert R["size"]["y2025"] > 4e7 and R["size"]["y2050"] > 5.2e7

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG\||(?:DOI|DOI_URL|BLOG_URL)\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "The largest city on Earth: six thousand years of the world's biggest cities",
        "slug": "largest-cities",
        "excerpt": f"From Uruk to Dhaka: I followed the title of the world's largest city through {s['n_snaps']} snapshots from 3700 BC to 2050. {R['n_crown_sole']} cities have held it, Chinese capitals for most of seven centuries, London for about {R['london']['years_est']} years, and the centre of the urban world has wandered from Mesopotamia to the Atlantic and back to Asia.",
        "seo_description": f"The world's largest city from 3700 BC to 2050: {R['n_crown_sole']} cities from Uruk to Dhaka, London's century and the path of the urban world's centre.",
        "tags": ["cities", "urban history", "maps", "data visualisation", "history", "population", "London", "Chandler", "World Urbanization Prospects"],
        "header_alt": f"Title card reading 'The largest city on Earth' in black, red and gold on pale paper, beside a world map with dots for every city that has been the world's largest and a line coloured from purple to yellow tracing the centre of the 25 largest cities from Mesopotamia across Central Asia, up over the Arctic and down to Tibet, and below it a line chart of the largest city's population rising from Uruk to Dhaka."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/largest-cities_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "raw"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"largest-cities/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"largest-cities/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "largest-cities/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": PAPER_TITLE,
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Historical data: Reba, Reitsma and Seto (2016), Scientific Data 3, 160034, from Chandler (1987) and Modelski (2003), CC BY 4.0. Modern data: UN World Urbanization Prospects 2025, CC BY 3.0 IGO.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["cities", "urbanisation", "urban history", "historical demography", "largest cities", "Chandler", "Modelski", "World Urbanization Prospects", "Degree of Urbanisation", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": REBA_DOI, "relation": "isDerivedFrom", "resource_type": "publication-article"},
                                 {"identifier": FIG["chandler"], "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": FIG["ancient"], "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": FIG["modern"], "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": WUP_URL, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
