/* Backtests page. Reads the JSON results the research scripts write (copied to data/research/). */
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  function el(tag, attrs, ...kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k === "style") n.style.cssText = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return n;
  }
  const svgEl = (tag, attrs) => {
    const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v);
    return n;
  };
  const kr = (v) => v == null ? "–" : Math.round(v).toLocaleString("en-US") + " kr";
  const pct = (v, d = 1) => v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d) + "%";
  const share = (v) => v == null ? "–" : `${v}%`;
  const signCls = (v) => v > 0 ? "up" : v < 0 ? "down" : "";
  const fmtDate = (s) => new Date(s + "T12:00:00Z").toLocaleDateString("en-GB", { month: "short", year: "numeric" });
  const tip = $("#tip");
  const REAL_LABEL = "80,000 kr after the last 10 years, after inflation";
  const realTitle = (rows) => {
    const r = rows.find((x) => x.inflation_10y_pct != null);
    return r ? `80,000 kr put in 10 years ago, valued today and shrunk by Danish inflation (${r.inflation_10y_pct}% over the 10 years, Statistics Denmark), so it is in the same money as the 80,000 kr you put in. Above 80,000 kr means you can buy more than you started with.` : null;
  };
  const realCol = (rows) => ({ label: REAL_LABEL, num: true, wide: true, title: realTitle(rows), get: (r) => r.value_of_80k_after_10y_real_kr,
    fmt: kr, cls: (r) => r.value_of_80k_after_10y_real_kr == null ? "" : signCls(r.value_of_80k_after_10y_real_kr - 80000) });

  function table(t, cols, rows, highlight) {
    t.replaceChildren(
      el("thead", {}, el("tr", {}, cols.map((c) => el("th", { class: (c.num ? "num" : "") + (c.wide ? " wide" : ""), text: c.label, title: c.title })))),
      el("tbody", {}, rows.map((r) => el("tr", { class: highlight && highlight(r) ? "chosen" : "" },
        cols.map((c) => {
          const v = c.get(r);
          return el("td", { class: (c.num ? "num " : "") + (c.cls ? c.cls(r) : ""), text: c.fmt ? c.fmt(v) : v });
        })))));
  }

  function seg(host, items, onPick) {
    host.replaceChildren(...items.map((it, i) => el("button", { type: "button", "aria-pressed": String(i === 0), text: it.label,
      onclick: (e) => { host.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", b === e.currentTarget)); onPick(it.value); } })));
  }

  function showTip(evt, nodes) {
    tip.replaceChildren(...nodes.filter(Boolean));
    tip.hidden = false;
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let x = evt.clientX + 14, y = evt.clientY + 14;
    if (x + w > innerWidth - 8) x = evt.clientX - w - 14;
    if (y + h > innerHeight - 8) y = evt.clientY - h - 14;
    tip.style.position = "fixed"; tip.style.left = x + "px"; tip.style.top = y + "px";
  }
  const hideTip = () => { tip.hidden = true; };

  const load = (name) => fetch(`data/research/${name}.json?v=${Date.now()}`).then((r) => r.ok ? r.json() : null).catch(() => null);
  Promise.all(["backtest_results", "decision", "plan_lsb", "horizon", "timing", "house_5y"].map(load)).then(([bt, dec, plan, hor, tim, house]) => {
    if (bt) rules(bt, dec);
    if (plan) planLsb(plan);
    if (hor) horizon(hor);
    if (tim) timing(tim);
    if (house) loan(house);
    notes({ "Strategy rules": bt && bt.caveats, "80,000 kr plan": plan && plan.notes, "Saving for a house": hor && hor.notes,
      "When to start": tim && tim.notes, "Paying down a loan": house && house.notes });
    if (bt) $("#gen").textContent = `Strategy backtest run ${new Date(bt.generated).toLocaleDateString("en-GB", { dateStyle: "medium" })}.`;
  });

  // ── Strategy rules ────────────────────────────────────────────────────────
  function rules(bt, dec) {
    let cap = 10000, showAll = false;
    $("#rules-sub").textContent = `${bt.results.filter((r) => r.capital === 10000).length - 3} variants of the trading rules, ${fmtDate(bt.period[0])} to ${fmtDate(bt.period[1])}, after Saxo fees and tax. Each dot is one variant; up is better, left is safer. The last column takes Danish inflation off, so 80,000 kr means you only kept up with prices.`;
    if (dec) $("#rules-why").replaceChildren(...dec.why.map((w) => el("li", { text: w })));
    const chosenName = "4 stocks, quarterly, keep top 8, no filter, 12-1m momentum";
    const kind = (r) => r.name === chosenName ? "chosen" : r.name.startsWith("S&P 500") ? "index" : r.name.startsWith("Same 38") ? "baseline"
      : r.name.includes("NO COSTS") ? "nocost" : "variant";
    $("#rules-legend").replaceChildren(
      el("span", { style: "--c:var(--skill)", text: "Chosen rules" }),
      el("span", { style: "--c:var(--momentum)", text: "Same stocks, bought and held" }),
      el("span", { class: "dash", style: "--c:var(--spy)", text: "Index fund" }),
      el("span", { class: "dot", style: "--c:var(--ink-2)", text: "Other variants" }));
    seg($("#rules-cap"), [{ label: "10,000 kr", value: 10000 }, { label: "100,000 kr", value: 100000 }], (v) => { cap = v; draw(); });
    $("#rules-more").onclick = () => { showAll = !showAll; draw(); };

    function draw() {
      const rows = bt.results.filter((r) => r.capital === cap && kind(r) !== "nocost");
      scatter(rows, kind);
      const sorted = rows.slice().sort((a, b) => (kind(b) !== "variant") - (kind(a) !== "variant") || b.sharpe - a.sharpe);
      const vis = showAll ? sorted : sorted.slice(0, 15);
      table($("#rules-table"), [
        { label: "Rules", get: (r) => r.name.replace(", no filter", "").replace(", trend filter", ", 200-day filter") },
        { label: "Per year", num: true, get: (r) => r.cagr_pct, fmt: pct },
        { label: "2012–18", num: true, get: (r) => r.cagr_2012_2018_pct, fmt: pct },
        { label: "2019–26", num: true, get: (r) => r.cagr_2019_now_pct, fmt: pct },
        { label: "Worst drop", num: true, get: (r) => r.max_drawdown_pct, fmt: (v) => pct(v, 0) },
        { label: "Worst year", num: true, get: (r) => r.worst_year_pct, fmt: (v) => pct(v, 0) },
        { label: "Costs a year", num: true, get: (r) => r.costs_pct_per_year, fmt: (v) => v == null ? "–" : v.toFixed(2) + "%" },
        { label: "Sharpe", num: true, get: (r) => r.sharpe, fmt: (v) => v == null ? "–" : v.toFixed(2) },
        realCol(rows),
      ], vis, (r) => kind(r) === "chosen");
      $("#rules-more").textContent = showAll ? "Show the top 15" : `Show all ${rows.length} rows`;
    }
    draw();
    let raf; addEventListener("resize", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(draw); });
  }

  function scatter(rows, kind) {
    const host = $("#rules-chart");
    host.replaceChildren();
    const W = host.clientWidth, H = host.clientHeight, narrow = W < 560;
    const m = { l: 48, r: narrow ? 16 : 150, t: 12, b: 40 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const xs = rows.map((r) => -r.max_drawdown_pct), ys = rows.map((r) => r.cagr_pct);
    const x0 = Math.floor(Math.min(...xs) / 5) * 5, x1 = Math.ceil(Math.max(...xs) / 5) * 5;
    const y0 = Math.floor(Math.min(...ys, 0) / 5) * 5, y1 = Math.ceil(Math.max(...ys) / 5) * 5;
    const x = (v) => m.l + (v - x0) / (x1 - x0) * iw, y = (v) => m.t + ih - (v - y0) / (y1 - y0) * ih;
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true" });
    for (let v = y0; v <= y1; v += 5) {
      svg.append(svgEl("line", { class: "grid-line", x1: m.l, x2: m.l + iw, y1: y(v), y2: y(v) }));
      const t = svgEl("text", { class: "axis-text", x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }); t.textContent = v + "%"; svg.append(t);
    }
    for (let v = x0; v <= x1; v += 5) {
      const t = svgEl("text", { class: "axis-text", x: x(v), y: m.t + ih + 18, "text-anchor": "middle" }); t.textContent = "−" + v + "%"; svg.append(t);
    }
    const xl = svgEl("text", { class: "axis-text", x: m.l + iw / 2, y: H - 4, "text-anchor": "middle" }); xl.textContent = "Worst drop"; svg.append(xl);
    const yl = svgEl("text", { class: "axis-text", x: 4, y: m.t + 2, "text-anchor": "start" }); yl.textContent = ""; svg.append(yl);
    const order = ["variant", "index", "baseline", "chosen"];
    const style = { variant: [css("--ink-2"), 4, 0.35], index: [css("--spy"), 6, 1], baseline: [css("--momentum"), 6, 1], chosen: [css("--skill"), 7, 1] };
    const labels = [];
    for (const k of order) for (const r of rows.filter((r) => kind(r) === k)) {
      const [col, rad, op] = style[k];
      const cx = x(-r.max_drawdown_pct), cy = y(r.cagr_pct);
      const c = svgEl("circle", { cx, cy, r: rad, fill: k === "index" ? css("--panel") : col, "fill-opacity": op,
        stroke: k === "index" ? col : css("--panel"), "stroke-width": k === "index" ? 2.5 : 1.5, "stroke-dasharray": k === "index" ? "3 2" : "none" });
      const hit = svgEl("circle", { cx, cy, r: Math.max(rad + 6, 10), fill: "transparent" });
      hit.style.cursor = "default";
      hit.addEventListener("pointermove", (e) => showTip(e, [el("div", { class: "d", text: r.name }),
        el("div", { class: "row" }, el("span", { text: "Per year" }), el("b", { text: pct(r.cagr_pct) })),
        el("div", { class: "row" }, el("span", { text: "Worst drop" }), el("b", { text: pct(r.max_drawdown_pct, 0) })),
        el("div", { class: "row" }, el("span", { text: "Costs a year" }), el("b", { text: (r.costs_pct_per_year ?? 0).toFixed(2) + "%" })),
        r.value_of_80k_after_10y_real_kr == null ? null : el("div", { class: "row" }, el("span", { text: "80,000 kr, 10 years, after inflation" }), el("b", { text: kr(r.value_of_80k_after_10y_real_kr) }))]));
      hit.addEventListener("pointerleave", hideTip);
      svg.append(c, hit);
      if (k !== "variant" && !narrow) labels.push({ cx, cy, text: k === "chosen" ? "Chosen rules" : k === "index" ? "Index fund" : "Same stocks, held" });
    }
    labels.sort((a, b) => a.cy - b.cy);
    for (let i = 1; i < labels.length; i++) if (labels[i].cy - labels[i - 1].cy < 16) labels[i].cy = labels[i - 1].cy + 16;
    for (const l of labels) {
      const t = svgEl("text", { class: "end-label", x: l.cx + 12, y: l.cy + 4 }); t.textContent = l.text; svg.append(t);
    }
    host.append(svg);
  }

  // ── 80,000 kr plan ────────────────────────────────────────────────────────
  function planLsb(d) {
    $("#plan-sub").textContent = `Invested ${fmtDate(d.period[0])}, measured to ${fmtDate(d.period[1])}, with Lån & Spar's fees, holding fee on foreign shares and 17% tax. The last column takes Danish inflation off, so 80,000 kr means you only kept up with prices.`;
    const rows = d.rows.slice().sort((a, b) => a.cagr_pct - b.cagr_pct);
    table($("#plan-table"), [
      { label: "Plan", get: (r) => r.plan },
      { label: "Per year", num: true, get: (r) => r.cagr_pct, fmt: pct },
      { label: "Worst drop", num: true, get: (r) => r.max_drawdown_pct, fmt: (v) => pct(v, 0) },
      { label: "Worst year", num: true, get: (r) => r.worst_year_pct, fmt: (v) => pct(v, 0) },
      { label: "Costs a year", num: true, get: (r) => r.costs_pct_per_year, fmt: (v) => v == null ? "–" : v.toFixed(2) + "%" },
      realCol(rows),
    ], rows, (r) => r.plan.startsWith("Global index"));
  }

  // ── Horizon ───────────────────────────────────────────────────────────────
  function horizon(d) {
    let plan = "Index fund";
    const first = d.rows[0];
    $("#horizon-sub").textContent = `80,000 kr, every start month from ${fmtDate(d.period[0])}. A savings account at 2% after 37% tax turns it into ${kr(first.savings_kr)} after a year and ${kr(d.rows.find((r) => r.years === 5).savings_kr)} after five.`;
    $("#horizon-legend").replaceChildren(
      el("span", { style: "--c:var(--skill)", text: "Beat the savings account" }),
      el("span", { style: "--c:var(--momentum)", text: "Ended below 80,000 kr" }));
    seg($("#horizon-plan"), [{ label: "Invest all", value: "Index fund" }, { label: "Move to savings at the end", value: "Index fund, glide to savings" }],
      (v) => { plan = v; draw(); });
    function draw() {
      let rows = d.rows.filter((r) => r.plan === plan);
      if (plan !== "Index fund") rows = [d.rows.find((r) => r.plan === "Index fund" && r.years === 1), ...rows];
      lines($("#horizon-chart"), rows);
      table($("#horizon-table"), [
        { label: "Years until buying", num: true, get: (r) => r.years },
        { label: "Savings account", num: true, get: (r) => r.savings_kr, fmt: kr },
        { label: "Typical result", num: true, get: (r) => r.median_kr, fmt: kr },
        { label: "Worst 1 in 10", num: true, get: (r) => r.worst_10pct_kr, fmt: kr },
        { label: "Worst", num: true, get: (r) => r.worst_kr, fmt: kr },
        { label: "Beat savings", num: true, get: (r) => r.pct_beat_savings, fmt: share },
        { label: "Below 80,000 kr", num: true, get: (r) => r.pct_below_80k, fmt: share },
        { label: "Lost over 20%", num: true, get: (r) => r.pct_lost_over_20pct, fmt: share },
      ], rows);
    }
    draw();
    let raf; addEventListener("resize", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(draw); });
  }

  function lines(host, rows) {
    host.replaceChildren();
    const W = host.clientWidth, H = host.clientHeight, narrow = W < 560;
    const m = { l: 44, r: narrow ? 16 : 170, t: 12, b: 40 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const n = rows.length;
    const x = (i) => m.l + i / (n - 1) * iw, y = (v) => m.t + ih - v / 100 * ih;
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true" });
    for (let v = 0; v <= 100; v += 25) {
      svg.append(svgEl("line", { class: "grid-line", x1: m.l, x2: m.l + iw, y1: y(v), y2: y(v) }));
      const t = svgEl("text", { class: "axis-text", x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }); t.textContent = v + "%"; svg.append(t);
    }
    rows.forEach((r, i) => {
      const t = svgEl("text", { class: "axis-text", x: x(i), y: m.t + ih + 18, "text-anchor": "middle" }); t.textContent = r.years; svg.append(t);
    });
    const xl = svgEl("text", { class: "axis-text", x: m.l + iw / 2, y: H - 4, "text-anchor": "middle" }); xl.textContent = "Years until you buy"; svg.append(xl);
    const series = [["pct_beat_savings", "--skill", "Beat savings"], ["pct_below_80k", "--momentum", "Below 80,000 kr"]];
    const ends = [];
    for (const [key, col, label] of series) {
      svg.append(svgEl("polyline", { points: rows.map((r, i) => `${x(i)},${y(r[key])}`).join(" "), fill: "none", stroke: css(col), "stroke-width": 2, "stroke-linejoin": "round" }));
      rows.forEach((r, i) => svg.append(svgEl("circle", { cx: x(i), cy: y(r[key]), r: 3.5, fill: css(col), stroke: css("--panel"), "stroke-width": 1.5 })));
      ends.push({ y: y(rows[n - 1][key]), text: `${label} ${rows[n - 1][key]}%` });
    }
    if (!narrow) {
      ends.sort((a, b) => a.y - b.y);
      if (ends[1].y - ends[0].y < 16) ends[1].y = ends[0].y + 16;
      for (const e of ends) { const t = svgEl("text", { class: "end-label", x: m.l + iw + 10, y: e.y + 4 }); t.textContent = e.text; svg.append(t); }
    }
    rows.forEach((r, i) => {
      const hit = svgEl("rect", { x: x(i) - iw / (n - 1) / 2, y: m.t, width: iw / (n - 1), height: ih, fill: "transparent" });
      hit.addEventListener("pointermove", (e) => showTip(e, [el("div", { class: "d", text: `${r.years} year${r.years > 1 ? "s" : ""} until buying` }),
        el("div", { class: "row" }, el("span", { text: "Beat savings" }), el("b", { text: r.pct_beat_savings + "%" })),
        el("div", { class: "row" }, el("span", { text: "Below 80,000 kr" }), el("b", { text: r.pct_below_80k + "%" })),
        el("div", { class: "row" }, el("span", { text: "Typical result" }), el("b", { text: kr(r.median_kr) })),
        el("div", { class: "row" }, el("span", { text: "Worst" }), el("b", { text: kr(r.worst_kr) }))]));
      hit.addEventListener("pointerleave", hideTip);
      svg.append(hit);
    });
    host.append(svg);
  }

  // ── Timing ────────────────────────────────────────────────────────────────
  function timing(d) {
    $("#timing-sub").textContent = `80,000 kr for 5 years. A savings account ends at ${kr(d.savings_kr)}.`;
    table($("#timing-table"), [
      { label: "Plan", get: (r) => r.plan },
      { label: "Starting point", get: (r) => r.starts },
      { label: "Start dates", num: true, get: (r) => r.windows },
      { label: "Typical result", num: true, get: (r) => r.median_kr, fmt: kr },
      { label: "Worst 1 in 10", num: true, get: (r) => r.worst_10pct_kr, fmt: kr },
      { label: "Beat savings", num: true, get: (r) => r.pct_beat_savings, fmt: share },
      { label: "Below 80,000 kr", num: true, get: (r) => r.pct_below_80k, fmt: share },
    ], d.rows, (r) => r.plan === "All at once" && r.starts === "All starts");
  }

  // ── Loan ──────────────────────────────────────────────────────────────────
  function loan(d) {
    const indexes = [...new Set(d.rows.map((r) => r.index))];
    const rates = [...new Set(d.rows.map((r) => r.loan))];
    let idx = indexes[0], rate = rates[1] || rates[0];
    const w = d.windows;
    seg($("#loan-index"), indexes.map((v) => ({ label: v.replace(/ \(.*/, "") + " " + (v.match(/\((.*)\)/) || ["", ""])[1], value: v })), (v) => { idx = v; draw(); });
    seg($("#loan-rate"), [rates[1], rates[0], rates[2]].filter(Boolean).map((v) => ({ label: v.split(" ")[0], value: v })), (v) => { rate = v; draw(); });
    function draw() {
      const rows = d.rows.filter((r) => r.index === idx && r.loan === rate);
      $("#loan-sub").textContent = `80,000 kr, 5 years, loan rate ${rate}. ${w[idx][2]} start months from ${fmtDate(w[idx][0])}. Paying down the loan removes ${kr(rows[0].paydown_benchmark_kr)} of debt for certain.`;
      table($("#loan-table"), [
        { label: "Plan", get: (r) => r.plan.replace(/^[A-E]\s+/, "") },
        { label: "Typical result", num: true, get: (r) => r.median_kr, fmt: kr },
        { label: "Worst 1 in 10", num: true, get: (r) => r.worst_10pct_kr, fmt: kr },
        { label: "Worst", num: true, get: (r) => r.worst_kr, fmt: kr },
        { label: "Best", num: true, get: (r) => r.best_kr, fmt: kr },
        { label: "Beat paying down", num: true, get: (r) => r.pct_windows_beat_paydown, fmt: share },
        { label: "Below 80,000 kr", num: true, get: (r) => r.pct_windows_below_80k, fmt: share },
      ], rows, (r) => r.plan.startsWith("A"));
    }
    draw();
  }

  function notes(map) {
    const host = $("#notes");
    for (const [title, text] of Object.entries(map)) {
      if (!text) continue;
      host.append(el("details", { class: "note" }, el("summary", { text: title }), el("pre", { text: text.trim() })));
    }
  }
})();
