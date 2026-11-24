/* Paper trader dashboard. Reads data/dashboard.json written by run.py every weekday. */
(() => {
  "use strict";

  const SERIES = [
    { id: "skill", label: "Skill-scored", short: "Skill", cssVar: "--skill" },
    { id: "momentum", label: "Momentum only", short: "Momentum", cssVar: "--momentum" },
    { id: "index", label: "S&P 500 index fund", short: "Index", cssVar: "--spy", dash: true },
  ];
  const SECTOR_SHORT = {
    "generic": "General", "it-saas": "Software & internet", "semiconductors": "Semiconductors",
    "retail-ecommerce": "Retail", "pharma-healthcare": "Pharma & health", "banks": "Banks",
    "exchanges-payments": "Payments", "holdco-assetmgr": "Holding co.", "oil-gas": "Oil & gas",
    "fmcg-consumer": "Consumer staples", "infra-capitalgoods": "Industrials", "utilities-power": "Utilities",
    "auto": "Autos", "rail-freight": "Railroads", "waste-environmental": "Waste", "chemicals-cement": "Chemicals",
    "metals-mining": "Mining", "people-businesses": "Services", "insurance": "Insurance", "nbfc": "Lenders",
    "telecom-media": "Telecom & media", "aviation-hotels": "Travel", "shipping-logistics": "Logistics",
    "realestate-reit": "Real estate",
  };
  const CAT_LABEL = {
    business_quality: "Business quality", profitability: "Profitability", earnings_quality: "Earnings quality",
    balance_sheet: "Balance sheet", growth: "Growth", governance: "Governance", valuation: "Valuation", risk: "Risk",
  };

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

  // Portfolio amounts are in the run's reporting currency (D.currency); share prices stay in USD.
  let CCY = "USD";
  const money = (v, d = 0) => {
    if (v == null) return "–";
    const n = Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
    return CCY === "USD" ? "$" + n : CCY === "DKK" ? n + " kr" : n + " " + CCY;
  };
  const usd = (v) => v == null ? "–" : "$" + Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const compact = (v, step) => {
    const k = v >= 1000 ? (v / 1000).toFixed(step < 1000 ? 1 : 0) + "k" : String(v);
    return CCY === "USD" ? "$" + k : CCY === "DKK" ? k + " kr" : k;
  };
  const pct = (v, d = 1) => v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d) + "%";
  const pts = (v) => Math.abs(v).toFixed(1) + (Math.abs(v).toFixed(1) === "1.0" ? " point" : " points");
  const signCls = (v) => v > 0 ? "up" : v < 0 ? "down" : "";
  const fmtDate = (s, opts = { day: "numeric", month: "short", year: "numeric" }) =>
    new Date(s + "T12:00:00Z").toLocaleDateString("en-GB", opts);
  const short = (k) => SECTOR_SHORT[k] || k || "–";

  let D = null;

  // ── boot ──────────────────────────────────────────────────────────────────
  fetch("data/dashboard.json?v=" + Date.now())
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((d) => { D = d; CCY = d.currency || "USD"; render(); })
    .catch((err) => { console.error("render failed", err && err.stack);
      $("#stamp").textContent = "No data yet";
      $("#verdict").textContent = "Waiting for the first trading day.";
      $("#lede").textContent = "The bot runs every weekday after the US market closes. Once it has run, the portfolios, scores and trades appear here. To start it now, open the repository's Actions tab and run “Daily paper trade”.";
      document.querySelectorAll("section.panel, .race").forEach((s) => (s.hidden = true));
    });

  function render() {
    const gen = new Date(D.generated_at);
    $("#stamp").replaceChildren(el("span", { class: "live", "aria-hidden": "true" }),
      `Prices as of ${fmtDate(D.as_of)}`);
    $("#gen").textContent = `Last run ${gen.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}. Skill version: ${D.skill.version}`;
    $("#chart-title").textContent = `Value of ${money(D.config.starting_cash)}`;
    if (CCY !== "USD" && D.fx_usd) {
      $("#fx-note").textContent = `Amounts are in ${CCY === "DKK" ? "Danish kroner" : CCY}. The stocks trade in US dollars, so values convert at each day's rate (today 1 USD = ${D.fx_usd.toFixed(2)} ${CCY === "DKK" ? "kr" : CCY}) and currency moves count, as they would for you.`;
      $("#fx-note").hidden = false;
    }
    if (D.demo) {
      const b = $("#banner"); b.hidden = false;
      b.textContent = "Demo data. These numbers are simulated to preview the site. Real results replace them after the first live run.";
    }
    renderHero(); renderRace(); renderChart(); renderHoldings("skill"); renderToday(); renderBoard(); renderLog(); renderRules();
  }

  const strat = (id) => D.strategies.find((s) => s.id === id) || {};
  const stat = (id) => strat(id).stats || {};

  // ── hero verdict ────────────────────────────────────────────────────────
  function renderHero() {
    const s = stat("skill"), m = stat("momentum"), b = stat("index");
    const v = $("#verdict");
    const who = (cls, txt) => el("span", { class: "who " + cls, text: txt });
    if (!s.days || s.days < 2) {
      v.replaceChildren("Day one. ", who("skill", "Skill-scored"), ", ", who("momentum", "momentum"), " and the ",
        who("spy", "index fund"), ` each start with ${money(D.config.starting_cash)}.`);
    } else {
      const vsSpy = s.total_return_pct - b.total_return_pct, vsMom = s.total_return_pct - m.total_return_pct;
      const rel = (d) => (d >= 0 ? "ahead of " : "behind ");
      v.replaceChildren(who("skill", "Skill-scored"), " is ", rel(vsSpy), "the ", who("spy", "index fund"), ` by ${pts(vsSpy)} and `,
        rel(vsMom), who("momentum", "momentum"), ` by ${pts(vsMom)}.`);
    }
    const start = D.strategies[0].started;
    const pend = D.strategies.reduce((n, x) => n + (x.pending || []).length, 0);
    $("#lede").textContent = (s.days > 1)
      ? `${s.days} trading days since ${fmtDate(start)}. Each portfolio started with ${money(D.config.starting_cash)} on a simulated Saxo aktiesparekonto, paying real fees, currency costs and tax. Skill-scored is now ${money(s.value)}, Momentum only ${money(m.value)}, and the index fund ${money(b.value)}.`
      : `Each portfolio starts with ${money(D.config.starting_cash)} on a simulated Saxo aktiesparekonto, paying real fees, currency costs and tax. Orders are decided after the US close and fill at the next open` + (pend ? `: ${pend} orders are waiting for it now.` : ".");
  }

  // ── race table ──────────────────────────────────────────────────────────
  function renderRace() {
    const tb = $("#race tbody"); tb.replaceChildren();
    const best = Math.max(...SERIES.map((x) => stat(x.id).total_return_pct ?? -1e9));
    for (const sr of SERIES) {
      const st = stat(sr.id);
      const lead = st.days > 1 && st.total_return_pct === best ? el("span", { class: "lead-badge", text: "Leading" }) : null;
      tb.append(el("tr", {},
        el("td", {}, el("span", { class: "key" + (sr.dash ? " spy" : ""), style: `border-color:var(${sr.cssVar})` }), sr.label, lead),
        el("td", { class: "num big", text: money(st.value) }),
        el("td", { class: "num big " + signCls(st.total_return_pct), text: pct(st.total_return_pct, 2) }),
        el("td", { class: "num " + signCls(st.day_pct), text: pct(st.day_pct, 2) }),
        el("td", { class: "num hide-sm", text: money(strat(sr.id).after_tax_value) }),
        el("td", { class: "num hide-sm", text: money(strat(sr.id).costs_total) }),
        el("td", { class: "num hide-sm", text: st.max_drawdown_pct != null ? pct(st.max_drawdown_pct) : "–" }),
        el("td", { class: "num hide-sm", text: st.sharpe != null ? st.sharpe.toFixed(2) : "–" }),
      ));
    }
  }

  // ── equity chart ────────────────────────────────────────────────────────
  let range = 0;
  function renderChart() {
    const lg = $("#legend"); lg.replaceChildren(...SERIES.map((s) => el("span", { class: s.dash ? "dash" : "", style: `--c:var(${s.cssVar})`, text: s.label })));
    $("#ranges").onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      range = +b.dataset.range;
      $("#ranges").querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
      drawChart();
    };
    const t = $("#equity-table");
    t.replaceChildren(el("thead", {}, el("tr", {}, el("th", { text: "Date" }), ...SERIES.map((s) => el("th", { class: "num", text: s.label })))),
      el("tbody", {}, ...D.equity.slice().reverse().map((r) => el("tr", {}, el("td", { text: fmtDate(r.date) }),
        ...SERIES.map((s) => el("td", { class: "num", text: money(r[s.id], 2) }))))));
    drawChart();
    let raf; window.addEventListener("resize", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(drawChart); });
  }

  function drawChart() {
    const host = $("#chart"), tip = $("#tip");
    const rows = range ? D.equity.slice(-range) : D.equity;
    host.replaceChildren(); tip.hidden = true;
    if (!rows.length) return;
    const W = host.clientWidth, H = host.clientHeight;
    const narrow = W < 560;
    const m = { l: narrow ? 44 : 56, r: narrow ? 64 : 96, t: 12, b: 28 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const vals = rows.flatMap((r) => SERIES.map((s) => r[s.id])).filter((v) => v != null);
    const start = D.config.starting_cash || 10000;
    let lo = Math.min(...vals, start), hi = Math.max(...vals, start);
    const pad = (hi - lo) * 0.08 || hi * 0.02; lo -= pad; hi += pad;
    const step = niceStep((hi - lo) / 5);
    lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
    const n = rows.length;
    const x = (i) => m.l + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
    const y = (v) => m.t + ih - ((v - lo) / (hi - lo)) * ih;

    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true" });
    for (let v = lo; v <= hi + 1e-6; v += step) {
      svg.append(svgEl("line", { class: "grid-line", x1: m.l, x2: m.l + iw, y1: y(v), y2: y(v) }));
      const t = svgEl("text", { class: "axis-text", x: m.l - 8, y: y(v) + 4, "text-anchor": "end" });
      t.textContent = compact(v, step); svg.append(t);
    }
    if (start > lo && start < hi) svg.append(svgEl("line", { class: "start-line", x1: m.l, x2: m.l + iw, y1: y(start), y2: y(start) }));
    // x labels: ~5 evenly spaced
    const ticks = Math.min(narrow ? 3 : 5, n);
    for (let k = 0; k < ticks; k++) {
      const i = ticks === 1 ? 0 : Math.round((k / (ticks - 1)) * (n - 1));
      const t = svgEl("text", { class: "axis-text", x: x(i), y: H - 6, "text-anchor": k === 0 ? "start" : k === ticks - 1 ? "end" : "middle" });
      t.textContent = fmtDate(rows[i].date, { day: "numeric", month: "short" }); svg.append(t);
    }
    // lines (benchmark first so strategies sit on top)
    const ends = [];
    for (const s of [...SERIES].reverse()) {
      const d = rows.map((r, i) => r[s.id] == null ? null : `${x(i).toFixed(1)},${y(r[s.id]).toFixed(1)}`).filter(Boolean);
      if (!d.length) continue;
      svg.append(svgEl("polyline", { points: d.join(" "), fill: "none", stroke: css(s.cssVar), "stroke-width": 2,
        "stroke-linejoin": "round", "stroke-linecap": "round", "stroke-dasharray": s.dash ? "5 4" : "none" }));
      const last = rows[n - 1][s.id];
      if (n === 1) svg.append(svgEl("circle", { cx: x(0), cy: y(last), r: 4, fill: css(s.cssVar) }));
      ends.push({ s, v: last, y: y(last) });
    }
    // direct end labels, nudged apart
    ends.sort((a, b) => a.y - b.y);
    for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 16) ends[i].y = ends[i - 1].y + 16;
    for (const e of ends) {
      const t = svgEl("text", { class: "end-label", x: m.l + iw + 8, y: e.y + 4 });
      t.textContent = narrow ? money(e.v) : `${e.s.short || e.s.label} ${money(e.v)}`;
      svg.append(t);
    }
    const cross = svgEl("line", { class: "cross", y1: m.t, y2: m.t + ih, visibility: "hidden" });
    const dots = SERIES.map((s) => svgEl("circle", { r: 4, fill: css(s.cssVar), stroke: css("--panel"), "stroke-width": 2, visibility: "hidden" }));
    svg.append(cross, ...dots);
    host.append(svg);

    // hover / keyboard crosshair
    let cur = -1;
    const show = (i) => {
      cur = Math.max(0, Math.min(n - 1, i));
      const r = rows[cur], cx = x(cur);
      cross.setAttribute("x1", cx); cross.setAttribute("x2", cx); cross.setAttribute("visibility", "visible");
      SERIES.forEach((s, k) => {
        if (r[s.id] == null) return dots[k].setAttribute("visibility", "hidden");
        dots[k].setAttribute("cx", cx); dots[k].setAttribute("cy", y(r[s.id])); dots[k].setAttribute("visibility", "visible");
      });
      tip.replaceChildren(el("div", { class: "d", text: fmtDate(r.date, { weekday: "short", day: "numeric", month: "short", year: "numeric" }) }),
        ...SERIES.map((s) => el("div", { class: "row" },
          el("span", {}, el("i", { class: s.dash ? "dash" : "", style: `--c:var(${s.cssVar})` }), s.label),
          el("b", { text: money(r[s.id], 2) }))));
      tip.hidden = false;
      const panel = host.parentElement.getBoundingClientRect(), hb = host.getBoundingClientRect();
      const tw = tip.offsetWidth;
      let left = hb.left - panel.left + cx + 14;
      if (left + tw > panel.width - 8) left = hb.left - panel.left + cx - tw - 14;
      tip.style.left = Math.max(8, left) + "px";
      tip.style.top = (hb.top - panel.top + 8) + "px";
    };
    const hide = () => { tip.hidden = true; cross.setAttribute("visibility", "hidden"); dots.forEach((d) => d.setAttribute("visibility", "hidden")); };
    const idxAt = (clientX) => {
      const px = clientX - host.getBoundingClientRect().left;
      return Math.round(((px - m.l) / iw) * (n - 1));
    };
    host.onpointermove = (e) => show(idxAt(e.clientX));
    host.onpointerleave = hide;
    host.tabIndex = 0;
    host.onfocus = () => show(n - 1);
    host.onblur = hide;
    host.onkeydown = (e) => {
      if (e.key === "ArrowLeft") { show(cur - 1); e.preventDefault(); }
      if (e.key === "ArrowRight") { show(cur + 1); e.preventDefault(); }
    };
  }
  function niceStep(raw) {
    const p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
  }

  // ── holdings ────────────────────────────────────────────────────────────
  function renderHoldings(sid) {
    $("#hold-tabs").onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      $("#hold-tabs").querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
      renderHoldings(b.dataset.sid);
    };
    const s = strat(sid);
    const t = $("#holdings");
    const body = [];
    if (!s.holdings.length) {
      body.push(el("tr", {}, el("td", { colspan: 6, class: "empty",
        text: (s.pending || []).length ? "All cash for now. The orders below fill at the next market open." : "No positions. Nothing passes this portfolio's rules right now, so it holds cash." })));
    }
    for (const h of s.holdings) body.push(el("tr", {},
      el("td", {}, el("span", { class: "tick", text: h.ticker }), el("span", { class: "name", text: h.name })),
      el("td", { class: "num", text: `${h.shares}` }),
      el("td", { class: "num" }, money(h.value), el("span", { class: "name", text: h.weight_pct.toFixed(0) + "% of portfolio" })),
      el("td", { class: "num" }, el("span", { class: signCls(h.pnl_pct), text: pct(h.pnl_pct) }),
        el("span", { class: "name", text: "since " + fmtDate(h.entry_date, { day: "numeric", month: "short" }) })),
      el("td", { class: "num " + signCls(h.day_pct), text: pct(h.day_pct) }),
      el("td", {}, sid === "index" ? el("span", { class: "out", text: "Index fund" }) : scoreCell(h.composite, h.grade, false)),
    ));
    t.replaceChildren(
      el("thead", {}, el("tr", {}, el("th", { text: "Holding" }), el("th", { class: "num", text: "Shares" }), el("th", { class: "num", text: "Value" }),
        el("th", { class: "num", text: "Return after costs" }), el("th", { class: "num", text: "Today" }), el("th", { text: "Skill score" }))),
      el("tbody", {}, body));
    const pend = $("#pending"); pend.replaceChildren();
    if ((s.pending || []).length) {
      pend.append(el("h3", { text: "Orders for the next open" }),
        el("ul", { class: "events" }, s.pending.map((o) => el("li", {},
          el("span", { class: "what" }, el("span", { class: o.side > 0 ? "buy" : "sell", text: o.side > 0 ? "Buy " : "Sell " }),
            o.ticker + (o.side > 0 && o.budget_dkk ? ` for up to ${money(o.budget_dkk)}` : o.shares ? ` (${o.shares} shares)` : "")),
          el("span", { class: "why", text: o.reason })))));
    }
    const c = s.costs || {};
    $("#cash-line").textContent = `Cash ${money(s.cash)}. Fees paid so far ${money(s.costs_total)} (commission ${money(c.commission)}, currency ${money(c.fx_fee)}, spread ${money(c.slippage)}). Dividends received ${money(s.dividends_net)} after ${money(c.withholding)} US tax. ASK tax paid ${money(s.tax_paid)}, tax building up this year ${money(s.tax_accrued)}.`;
  }

  function scoreCell(c, grade, capped) {
    if (c == null) return el("span", { class: "out", text: "No score" });
    return el("div", { class: "score" },
      el("span", { class: "bar", "aria-hidden": "true" }, el("i", { class: capped ? "capped" : "", style: `width:${c * 10}%` })),
      el("b", { text: c.toFixed(1) }), el("span", { class: "grade", text: grade || "" }));
  }

  // ── today ───────────────────────────────────────────────────────────────
  function renderToday() {
    const ul = $("#today"); ul.replaceChildren();
    for (const a of D.alerts || []) ul.append(el("li", { class: "alert" }, el("span", { class: "what", text: a })));
    const todays = (D.trades || []).filter((t) => t.date === D.as_of);
    for (const t of todays) {
      ul.append(el("li", {},
        el("span", { class: "what" }, actionLabel(t), `${t.ticker}` + (t.value ? ` ${money(t.value)}` : ""),
          el("span", { class: "out", text: `  ${t.strategy}` })),
        el("span", { class: "why", text: t.reason + (t.fee && t.action !== "TAX" ? `. Fees ${money(t.fee, 2)}.` : "") })));
    }
    const pending = D.strategies.flatMap((x) => (x.pending || []).map((o) => ({ ...o, strategy: x.label })));
    if (pending.length) {
      ul.append(el("li", {}, el("span", { class: "what", text: `${pending.length} orders queued for the next open` }),
        el("span", { class: "why", text: pending.map((o) => `${o.side > 0 ? "buy" : "sell"} ${o.ticker} (${o.strategy})`).join(", ") })));
    }
    if (!ul.children.length) {
      ul.append(el("li", {}, el("span", { class: "what", text: "No trades today." }),
        el("span", { class: "why", text: `Trading happens once a ${D.config.rebalance === "quarterly" ? "quarter" : "month"}; between rebalances the bot only sells on a red-flag veto.` })));
    }
    const mv = D.universe.filter((r) => r.day_pct != null).sort((a, b) => b.day_pct - a.day_pct);
    if (mv.length > 2) {
      const best = mv[0], worst = mv[mv.length - 1];
      ul.append(el("li", {}, el("span", { class: "what", text: "Biggest moves on the watchlist" }),
        el("span", { class: "why", text: `${best.ticker} ${pct(best.day_pct)} and ${worst.ticker} ${pct(worst.day_pct)}` })));
    }
  }

  function actionLabel(t) {
    const map = { BUY: ["buy", "Bought "], SELL: ["sell", "Sold "], DIVIDEND: ["buy", "Dividend "], TAX: ["sell", "Tax "],
      SPLIT: ["out", "Split "], SKIPPED: ["out", "Skipped "] };
    const [cls, txt] = map[t.action] || ["out", t.action + " "];
    return el("span", { class: cls, text: txt });
  }

  // ── scoreboard ──────────────────────────────────────────────────────────
  let sortKey = "rank", sortDir = 1, open = new Set();
  function renderBoard() {
    $("#filter").oninput = drawBoard;
    drawBoard();
  }
  function drawBoard() {
    const q = $("#filter").value.trim().toLowerCase();
    let rows = D.universe.filter((r) => !q || [r.ticker, r.name, short(r.sector_key)].join(" ").toLowerCase().includes(q));
    const keyFn = {
      rank: (r) => r.skill_rank ?? 900 - (r.composite ?? 0),
      score: (r) => -(r.composite ?? -1),
      mom: (r) => -(r.mom_pct ?? -999),
      ticker: (r) => r.ticker,
    }[sortKey];
    rows = rows.slice().sort((a, b) => { const A = keyFn(a), B = keyFn(b); return (A < B ? -1 : A > B ? 1 : 0) * sortDir; });

    const head = (key, label, cls) => el("th", { class: cls || "" },
      el("button", { type: "button", "aria-sort": sortKey === key ? (sortDir === 1 ? "descending" : "ascending") : null,
        onclick: () => { if (sortKey === key) sortDir *= -1; else { sortKey = key; sortDir = 1; } drawBoard(); } , text: label }));
    const t = $("#board");
    const body = el("tbody");
    for (const r of rows) {
      const isOpen = open.has(r.ticker);
      const capped = (r.gates || []).some((g) => g.severity === "cap") && r.composite_raw > r.composite;
      const status = [];
      for (const sid of r.held_by || []) status.push(el("span", { class: "pill " + sid, text: sid === "skill" ? "Skill holds" : "Momentum holds" }));
      for (const g of r.gates || []) status.push(el("span", { class: "pill flag", text: g.severity === "veto" ? "Vetoed" : "Red flag" }));
      if (!status.length) {
        const ex = (r.excluded && r.excluded.skill) || [];
        const note = (r.notes || [])[0];
        status.push(el("span", { class: "out", text: ex.length ? capitalise(ex[0]) : note ? capitalise(note) : `Ranked, not in top ${D.config.holdings}` }));
      }
      const tr = el("tr", { class: "row", tabindex: "0", "aria-expanded": String(isOpen),
        onclick: () => toggle(r.ticker), onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(r.ticker); } } },
        el("td", {}, el("span", { class: "chev", "aria-hidden": "true", text: "›" }), r.skill_rank ? `#${r.skill_rank}` : "–"),
        el("td", {}, el("span", { class: "tick", text: r.ticker }), el("span", { class: "name", text: r.name })),
        el("td", { class: "hide-sm", text: short(r.sector_key) }),
        el("td", {}, scoreCell(r.composite, r.vetoed ? "Vetoed" : r.grade, capped)),
        el("td", { class: "num " + signCls(r.mom_pct), text: pct(r.mom_pct, 0) }),
        el("td", { class: "num hide-sm", text: r.share_cost_dkk != null ? money(r.share_cost_dkk) : "–" }),
        el("td", {}, status),
      );
      body.append(tr);
      if (isOpen) body.append(el("tr", { class: "detail" }, el("td", { colspan: 7 }, detail(r))));
    }
    t.replaceChildren(el("thead", {}, el("tr", {}, head("rank", "Rank"), head("ticker", "Stock"), el("th", { class: "hide-sm", text: "Sector" }),
      head("score", "Skill score"), head("mom", "12-month momentum", "num"), el("th", { class: "num hide-sm", text: "One share" }), el("th", { text: "Status" }))), body);
    if (!rows.length) t.append(el("tbody", {}, el("tr", {}, el("td", { colspan: 7, class: "empty", text: "No stocks match that filter." }))));
  }
  function toggle(tk) { open.has(tk) ? open.delete(tk) : open.add(tk); drawBoard(); }
  const capitalise = (s) => s.charAt(0).toUpperCase() + s.slice(1);

  function fmtMetric(m) {
    const v = m.value; if (v == null) return "–";
    const k = m.key;
    if (k.endsWith("_pct")) return v.toFixed(1) + "%";
    if (k.endsWith("_x") || k.endsWith("_3y") || k === "net_debt_to_ebitda" || k === "current_ratio") return v.toFixed(2) + "×";
    return String(v);
  }

  function detail(r) {
    const wrap = el("div", { class: "detail" });
    for (const g of r.gates || []) {
      wrap.append(el("div", { class: "gate" }, el("b", { text: g.severity === "veto" ? "Veto: " : `Score capped at ${g.cap}: ` }), g.label + ".",
        g.evidence ? el("span", { text: " " + g.evidence }) : null));
    }
    const cats = el("ul", { class: "cats" }, ...Object.entries(CAT_LABEL).map(([k, label]) => {
      const v = r.categories ? r.categories[k] : null;
      return el("li", {}, el("span", { text: label }),
        el("span", { class: "bar", "aria-hidden": "true" }, el("i", { style: `width:${(v || 0) * 10}%` })),
        el("span", { class: v == null ? "na" : "", text: v == null ? "n/a" : v.toFixed(1) }));
    }));
    const mt = el("table", { class: "metrics" },
      el("thead", {}, el("tr", {}, el("th", { text: "Measure" }), el("th", { class: "num", text: "Value" }),
        el("th", { class: "num hide-sm", text: "Sector band (poor / avg / good / excellent)" }), el("th", { class: "num", text: "Score" }))),
      el("tbody", {}, ...(r.metrics || []).map((m) => el("tr", {},
        el("td", { text: m.label }), el("td", { class: "num", text: fmtMetric(m) }),
        el("td", { class: "num hide-sm out", text: m.band || "" }), el("td", { class: "num", text: m.sub_score != null ? m.sub_score.toFixed(1) : "–" })))));
    wrap.append(el("div", { class: "detail-grid" },
      el("div", {}, el("h4", { text: `Scored as ${r.sector_label || short(r.sector_key)}` }), cats),
      el("div", {}, el("h4", { text: "What the skill measured" }), r.metrics && r.metrics.length ? mt : el("p", { text: "No fundamentals available for this company yet." }))));
    const notes = [];
    if (r.period) notes.push(`Statements: ${r.period}, fetched ${r.fundamentals_fetched}.`);
    if (r.confident === false) notes.push("Indicative score: the skill's judgement-based measures (moat, governance, management) are not automated, so coverage is below the skill's confidence floor.");
    if (r.skill_score != null) notes.push(`Ranking score ${r.skill_score} out of 100, blending skill score and momentum percentiles.`);
    if (notes.length) wrap.append(el("p", { text: notes.join(" ") }));
    return wrap;
  }

  // ── trade log ───────────────────────────────────────────────────────────
  let logFilter = "all", logLimit = 25;
  function renderLog() {
    $("#log-tabs").onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      logFilter = b.dataset.sid; logLimit = 25;
      $("#log-tabs").querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
      drawLog();
    };
    $("#log-more").onclick = () => { logLimit += 50; drawLog(); };
    drawLog();
  }
  function drawLog() {
    const all = (D.trades || []).filter((t) => logFilter === "all" || t.strategy === logFilter);
    const rows = all.slice(0, logLimit);
    $("#log").replaceChildren(
      el("thead", {}, el("tr", {}, el("th", { text: "Date" }), el("th", { text: "Trade" }), el("th", { class: "num", text: "Amount" }), el("th", { class: "num", text: "Fees" }),
        el("th", { class: "num hide-sm", text: "Share price" }), el("th", { text: "Reason" }))),
      el("tbody", {}, ...(rows.length ? rows.map((t) => el("tr", {},
        el("td", { text: fmtDate(t.date, { day: "numeric", month: "short" }) }),
        el("td", {}, actionLabel(t), el("span", { class: "tick", text: t.ticker }),
          el("span", { class: "name", text: t.strategy + (t.shares ? `, ${+t.shares} shares` : "") })),
        el("td", { class: "num", text: t.value ? money(t.value) : "–" }),
        el("td", { class: "num", text: t.fee ? money(t.fee, 2) : "–" }),
        el("td", { class: "num hide-sm", text: t.price ? (t.currency === "EUR" ? "€" + (+t.price).toFixed(2) : usd(t.price)) : "–" }),
        el("td", { class: "out", text: t.reason }))) : [el("tr", {}, el("td", { colspan: 6, class: "empty", text: "No trades yet. The first orders fill at the next market open." }))])));
    $("#log-more").hidden = all.length <= logLimit;
  }

  function renderRules() {
    const c = D.config, br = D.broker || {};
    $("#rules").textContent = `Each active portfolio holds ${c.holdings} stocks, bought in whole shares. It trades once a ${c.rebalance === "quarterly" ? "quarter" : "month"}: a holding stays while it ranks in the top ${c.keep_while_rank_within}, and only the gaps are filled, so there are no small top-up trades that would each pay a minimum fee. The one exception is a red-flag veto, which sells at the next open on any day.`;
    const costs = [
      ["Broker and account", `${br.broker || "Saxo"}, ${br.account || "aktiesparekonto"}`],
      ["Commission, US stocks", `${br.stock_commission_pct}% (at least $${br.stock_commission_min_usd})`],
      ["Commission, index fund", `${br.etf_commission_pct}% (at least €${br.etf_commission_min_eur})`],
      ["Currency exchange", `${br.fx_fee_pct}% each way`],
      ["Spread on a market order", `about ${br.slippage_pct}%`],
      ["US dividend tax", `${br.us_dividend_withholding_pct}% withheld, not refundable on an ASK`],
      ["ASK tax", `${br.ask_tax_pct}% of each year's gain, losses carried forward (deposit limit ${money(br.ask_deposit_cap_dkk)} in 2026)`],
      ["Index fund", br.etf ? `${br.etf.name}, ${br.etf.ter_pct}% a year` : "–"],
    ];
    $("#cost-table").replaceChildren(el("tbody", {}, costs.map(([k, v]) => el("tr", {}, el("th", { scope: "row", text: k }), el("td", { text: v })))));
    const R = D.research;
    if (R && R.rows) {
      $("#research-intro").textContent = `Tested on prices from ${fmtDate(R.period[0])} to ${fmtDate(R.period[1])}, starting with 10,000 kr and paying the costs above. All 38 stocks are today's winners, which flatters every row, so the fair comparison is the equal-weight hold of the same stocks.`;
      $("#research-table").replaceChildren(
        el("thead", {}, el("tr", {}, el("th", { text: "Approach" }), el("th", { class: "num", text: "Per year" }), el("th", { class: "num hide-sm", text: "2012–18" }),
          el("th", { class: "num hide-sm", text: "2019–26" }), el("th", { class: "num", text: "Worst drop" }), el("th", { class: "num hide-sm", text: "Costs a year" }))),
        el("tbody", {}, R.rows.map((r) => el("tr", { class: r.name.startsWith("Chosen") ? "chosen" : "" },
          el("td", { text: r.name }), el("td", { class: "num", text: pct(r.cagr_pct) }), el("td", { class: "num hide-sm", text: pct(r.cagr_2012_2018_pct) }),
          el("td", { class: "num hide-sm", text: pct(r.cagr_2019_now_pct) }), el("td", { class: "num", text: pct(r.max_drawdown_pct, 0) }),
          el("td", { class: "num hide-sm", text: r.costs_pct_per_year != null ? r.costs_pct_per_year.toFixed(2) + "%" : "–" })))));
      $("#research-why").replaceChildren(...R.why.map((w) => el("li", { text: w })));
      $("#research").hidden = false;
    }
  }
})();
