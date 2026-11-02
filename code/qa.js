// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8811; set PORT to change).
const { chromium } = require("playwright");
// MapLibre from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here,
// which also checks that the page degrades gracefully without them.
const ML = process.env.MAPLIBRE_DIST || "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/npm/node_modules/maplibre-gl/dist";
(async () => {
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js" }));
    await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to fetch|AJAXError/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8811) + "/index.html", { waitUntil: "networkidle" });
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    const snap = async y => { await p.evaluate(y => { const k = SITE.snaps.indexOf(y); setSnap(k); }, y); await p.waitForTimeout(900); };
    await shot("#atlas", "map_2025");
    for (const y of [-2800, -600, 200, 900, 1300, 1800, 1900, 1950, 2050]) { await snap(y); await shot("#atlas", "map_" + String(y).replace("-", "m")); }
    await p.click("#play"); await p.waitForTimeout(1600); await p.click("#play");
    await p.click('#scaleRow [data-s="abs"]'); await snap(1900); await shot("#atlas", "map_1900_abs"); await p.click('#scaleRow [data-s="rel"]');
    await p.click("#focusRow .btn:nth-child(4)"); await p.waitForTimeout(2600); await shot("#atlas", "jump_babylon");
    await p.fill("#q", "Hangzhou"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2600); await shot("#atlas", "search_hangzhou");
    await p.fill("#q", "London"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2600); await shot("#atlas", "search_london");
    await p.click("#focusRow .btn:last-child"); await p.waitForTimeout(1800);
    await p.click(".lyrBtn"); await p.waitForTimeout(300);
    for (const k of ["relief", "modern", "ref"]) await p.check(`.lyrPanel [data-k="${k}"]`);
    await p.waitForTimeout(800); await shot("#map", "layers_panel");
    for (const k of ["relief", "modern", "ref"]) await p.uncheck(`.lyrPanel [data-k="${k}"]`);
    await p.click(".lyrBtn");
    for (const c of ["crownChart", "reignTable", "countChart", "regionChart", "cogChart", "londonChart", "disTable", "seamTable", "riseChart", "covTable"]) await shot("#" + c, c);
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#crownChart", "dark_crown");
      await p.click("#theme"); await p.waitForTimeout(800);
    }
    await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    await p.keyboard.press("Escape"); await p.waitForTimeout(500);
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    const mapOk = await p.evaluate(() => !!(window.map && map.loaded && ready));
    console.log(nm, "horizontal overflow px:", ov, "map ready:", mapOk);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
