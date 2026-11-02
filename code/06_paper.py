"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23872999 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Largest_City"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
fx = {(f["city"], f["year"]): f["value"] for f in R["fixes"]}
assert [fx[("Teotihuacan", y)] for y in (-900, -800, -700, -600)] == [100000, 150000, 100000, 100000]      # the Teotihuacan example
assert sum(1 for c in R["cog"] if 1850 <= c["y"] <= 1970 and c["lon"] < 40) >= 6                             # "for about a century"
assert R["un"]["out_top10_2050"] == ["Seoul"]


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f in ("m1", "yr", "yrs"): return tex(fmt(v, f))
    return tex(str(v))


P = lambda v: f"{v / 1e6:.2f}m" if v >= 1e6 else f"{round(v):,}"
rows = "".join(f"{tex(yfmt(r['first']))} & {tex(yfmt(r['last'])) if r['last'] != r['first'] else ''} & {tex(r['label'])}{' (tie)' if r['tie'] else ''} & {r['n']} & {P(r['peak'])}\\\\\n" for r in R["reigns"])
TR = ("\\begin{longtable}{llp{6.6cm}rr}\\caption{Every run of consecutive snapshots with the same largest place (ties listed separately), with the highest population in the run.}\\label{tab:reigns}\\\\"
      "\\toprule From & To & Largest place & Snapshots & Peak\\\\\\midrule\\endfirsthead\\toprule From & To & Largest place & Snapshots & Peak\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}")
rows = "".join(f"{tex(yfmt(d['y']))} & {tex(', '.join(d['m']))} ({P(d['pm'])}) & {tex(', '.join(d['c']))} ({P(d['pc'])}) & {tex(', '.join(d['comb']))}\\\\\n" for d in R["disagree"])
TD = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Snapshots where both compilations have figures for at least " + str(R["method"]["min_places"]) + " places and name different leaders.}\\label{tab:dis}"
      "\\begin{tabular}{lp{4.3cm}p{3.6cm}p{3.6cm}}\\toprule Date & Modelski & Chandler & Combined\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
src = {"C": "Chandler", "M": "Modelski", "X": "Modelski 2000"}
rows = "".join(f"{src[f['src']]} & {tex(f['city'])} & {tex(yfmt(f['year'])) if f['year'] is not None else ''} & {format(f['value'], ',') if f['value'] is not None else 'location'} & {tex(f['why'])}\\\\\n" for f in R["fixes"])
TF = ("\\begin{longtable}{lllrp{6.2cm}}\\caption{Corrections to the V2 files.}\\label{tab:fixes}\\\\\\toprule Source & Place & Date & Figure & Reason\\\\\\midrule\\endfirsthead\\toprule Source & Place & Date & Figure & Reason\\\\\\midrule\\endhead\n"
      + rows.replace("\\\\\n", "\\\\\n") + "\\bottomrule\\end{longtable}")
rows = "".join(f"{tex(c['region'])} & " + " & ".join(f"{c[e]:,}" for e in R["eras"]) + "\\\\\n" for c in R["coverage"])
TC = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{Places with at least one estimate, by region and period (Chandler and Modelski, after corrections).}\\label{tab:cov}"
      "\\begin{tabular}{lrrrrr}\\toprule Region & " + " & ".join(tex(e) for e in R["eras"]) + "\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("REIGNS", TR), ("DIS", TD), ("FIXES", TF), ("COV", TC)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
for bad in ("DSIT", "DCMS"):
    assert bad not in txt
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
