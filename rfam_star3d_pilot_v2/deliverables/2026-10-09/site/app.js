/* Static site renderer. Every number shown comes from data/*.json written by
   scripts/export_site_data.py. Missing values render as "unavailable", never 0. */
"use strict";

const FILES = ["export_manifest", "funnel", "families", "pairs", "representatives", "construct_review",
  "exact_source_check", "run_status", "pair_summary", "new_pair_summary", "interactions", "regions",
  "candidate_7rex", "candidate_screening", "requirements_status", "test_results", "validation_checks",
  "results_status", "figures", "downloads", "survey_b", "rf00522_rows", "fresh_repro_other4", "method_differences"];
const UNAV = '<span class="unavail">unavailable</span>';

function esc(v) {
  return String(v).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function isMissing(v) { return v === undefined || v === null || v === "" || v === "NA" || v === "unavailable"; }
function show(v) { return isMissing(v) ? UNAV : esc(v); }
function num(v) { if (isMissing(v)) return null; const n = Number(v); return Number.isFinite(n) ? n : null; }
function $(id) { return document.getElementById(id); }

function frac(x, n) {
  const a = num(x), b = num(n);
  if (a === null || b === null) return UNAV;
  if (b === 0) return `${a} / 0 <span class="unavail">(no denominator)</span>`;
  return `${a} / ${b} <span class="meta">(${(100 * a / b).toFixed(1)}%)</span>`;
}

function tierTag(t) {
  if (isMissing(t)) return '<span class="tag na">tier unavailable</span>';
  const cls = t === "primary" ? "primary" : "exploratory";
  return `<span class="tag ${cls}">${esc(t.replace(/_/g, " "))}</span>`;
}

function table(payload, opts = {}) {
  if (!payload || payload.available === false) {
    return `<p class="unavail">Pending / unavailable${payload && payload.source ? ` (expected: <code>${esc(payload.source)}</code>)` : ""}.</p>`;
  }
  const cols = opts.columns || payload.columns || (payload.rows[0] ? Object.keys(payload.rows[0]) : []);
  const rows = opts.filter ? payload.rows.filter(opts.filter) : payload.rows;
  if (!rows.length) return '<p class="unavail">No rows.</p>';
  const head = cols.map(c => `<th scope="col">${esc(c)}</th>`).join("");
  const body = rows.map(r => "<tr>" + cols.map(c => {
    const v = r[c];
    if (c === "tier" || c === "family_decision") return `<td>${tierTag(v)}</td>`;
    if (c === "status" && !isMissing(v)) return `<td><strong>${esc(v)}</strong></td>`;
    const isNum = !isMissing(v) && /^-?\d+(\.\d+)?$/.test(String(v));
    const long = !isMissing(v) && String(v).length > 60;
    return `<td class="${isNum ? "num" : long ? "long" : ""}">${show(v)}</td>`;
  }).join("") + "</tr>").join("");
  const src = payload.source ? `<p class="meta">Source: <code>${esc(payload.source)}</code> &middot; ${rows.length} row(s) shown</p>` : "";
  return `<div class="tablewrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>${src}`;
}

function barRow(label, x, n, cls) {
  const a = num(x), b = num(n);
  let pct = 0, txt;
  if (a === null || b === null) txt = "unavailable";
  else if (b === 0) txt = "no eligible items";
  else { pct = 100 * a / b; txt = `${a} / ${b} (${pct.toFixed(0)}%)`; }
  return `<div class="barrow"><span>${esc(label)}</span>
    <div class="bar" role="img" aria-label="${esc(label)}: ${esc(txt)}"><span class="${cls}" style="width:${pct}%"></span></div>
    <span>${esc(txt)}</span></div>`;
}

/* ------------------------------------------------------------------ sections */
function renderKpis(D) {
  const f = D.funnel.counts, p = D.pairs.rows || [];
  const tiers = {};
  p.forEach(r => { tiers[r.tier] = (tiers[r.tier] || 0) + 1; });
  const items = [
    [f.families_in_inventory, "Rfam families inventoried"],
    [f.screen_status && f.screen_status.pass, "families passing automated screen"],
    [f.reviewed_total, "families manually reviewed (all sessions)"],
    [f.v3_accepted_primary_families, "new primary families found this session"],
    [p.length, "structure pairs in frozen cohort"],
    [tiers.primary, "primary pairs (interpretable)"],
    [D.run_status.current_rows, "current STAR3D steps logged"],
  ];
  $("kpis").innerHTML = items.map(([v, l]) => `<div class="kpi"><div class="v">${show(v)}</div><div class="l">${esc(l)}</div></div>`).join("");
}

function renderFunnel(D) {
  const f = D.funnel.counts;
  const total = f.families_in_inventory;
  const rows = [
    ["Families in inventory", total],
    ["Passed automated screen", f.screen_status.pass],
    ["Shortlisted for review", f.shortlisted.yes],
    ["Manually reviewed before this session", f.review_status.verified],
    ["Reviewed this session (2026-10-09)", f.v3_reviewed_families],
    ["Reviewed in total", f.reviewed_total],
    ["New primary families found this session", f.v3_accepted_primary_families],
  ];
  let html = rows.map(([l, v]) => barRow(l, v, total, "b-star")).join("");
  const dec = Object.entries(f.review_decision).map(([k, v]) => `<li><strong>${esc(k)}</strong>: ${show(v)} families</li>`).join("");
  html += `<p class="meta">Denominator: all families in <code>${esc(D.funnel.source)}</code>. The ${show(f.shortlisted.no_beyond_cap)} passing families beyond the original shortlist cap were reviewed this session (<code>${esc(D.funnel.v3_source || "")}</code>); ${show(f.v3_exploratory_only_families)} of them are exploratory-only and none met all primary criteria.</p>
    <details><summary>Review decisions (all families)</summary><ul>${dec}</ul></details>`;
  $("funnel").innerHTML = html;
}

function renderFamilies(D) {
  const rows = D.families.rows;
  const fill = (sel, key) => {
    [...new Set(rows.map(r => r[key]))].sort().forEach(v => {
      const o = document.createElement("option"); o.value = v; o.textContent = v; sel.appendChild(o);
    });
  };
  fill($("fam-screen"), "screen_status");
  fill($("fam-decision"), "review_decision");
  const draw = () => {
    const q = $("fam-search").value.trim().toLowerCase();
    const s = $("fam-screen").value, d = $("fam-decision").value;
    $("families-table").innerHTML = table(D.families, {
      filter: r => (!s || r.screen_status === s) && (!d || r.review_decision === d) &&
        (!q || Object.values(r).join(" ").toLowerCase().includes(q)),
    });
  };
  ["fam-search", "fam-screen", "fam-decision"].forEach(id => $(id).addEventListener("input", draw));
  draw();
}

function renderDataset(D) {
  $("pairs-table").innerHTML = table(D.pairs, { columns: ["pair_id", "tier", "query", "target", "primary_direction", "run_both_directions", "rationale"] });
  $("reps-table").innerHTML = table(D.representatives);
  $("construct-table").innerHTML = table(D.construct_review, { columns: ["rfam_acc", "key", "family_decision", "decision", "source", "construct_changes", "masked_label_seq_ids", "ligand_state", "evidence_strength", "engineering_status", "reason"] });
  $("exact-table").innerHTML = table(D.exact_source_check, { columns: ["key", "claimed_organism", "accession", "family_interval_len", "core_label_range", "internal_masked_positions", "verdict"] });
  $("screening-table").innerHTML = table(D.candidate_screening);
  $("surveyb-table").innerHTML = table(D.survey_b);
}

const CATS = [["same_partner", "same partner", "c-same"], ["different_partner", "different partner", "c-diff"],
  ["rfam_only", "rfam only", "c-rfam"], ["star3d_only", "star3d only", "c-star"], ["neither", "neither", "c-neither"]];

function pairCard(pid, groups, D) {
  const g0 = groups[0];
  let html = `<div class="card"><h4>${esc(pid)} ${tierTag(g0.tier)}</h4>`;
  groups.forEach(g => {
    const v = g.values;
    const st = Object.entries(g.status_counts).map(([k, n]) => `${esc(k)}: ${n}`).join(", ");
    html += `<p class="meta"><strong>${esc(g.direction)}</strong> run &middot; replicates ${g.completed_runs}/${g.runs} completed (${st}) &middot; replicates identical: ${show(g.replicates_identical)}</p>`;
    if (!v) { html += `<p class="unavail">No completed run: values unavailable.</p>`; return; }
    const total = num(v.source_row_len);
    const seg = CATS.map(([k, l, c]) => {
      const n = num(v[k]);
      return n && total ? `<span class="${c}" style="width:${100 * n / total}%" title="${esc(l)}: ${n}"></span>` : "";
    }).join("");
    html += `<div class="stack" role="img" aria-label="residue categories">${seg}</div>
      <div class="legend">${CATS.map(([k, l, c]) => `<span><span class="sw ${c}"></span>${esc(l)}: ${show(v[k])}</span>`).join("")}
      <span>total: ${show(v.source_row_len)} source-row residues (sum check: ${show(v.category_sum_check)})</span></div>
      <div class="classgrid">
        <div>${barRow("Assessable seed pairs reproduced by STAR3D", v.rfam_assessable_pairs_reproduced, v.rfam_pairs_structurally_assessable, "b-star")}</div>
        <div class="meta">Seed residue pairs: ${show(v.rfam_pairs)} (structurally assessable: ${show(v.rfam_pairs_structurally_assessable)}); STAR3D pairs: ${show(v.star3d_pairs)}; STAR3D RMSD ${show(v.star3d_rmsd)} &Aring;; Jaccard (unmasked) ${show(v.jaccard_pairs_unmasked)}; masked source/target residues ${show(v.source_masked)}/${show(v.target_masked)}</div>
      </div>`;
  });
  // interactions
  const side = $("side-filter").value;
  const ir = (D.interactions.rows || []).filter(r => r.pair_id === pid && r.comparison === "all_three_methods" && r.source_side === side);
  if (ir.length) {
    html += `<p><strong>Interaction preservation</strong> <span class="meta">(${esc(side)} structure as source; comparison all three methods; denominator = eligible unmasked interactions of that class)</span></p><div class="classgrid">`;
    ir.forEach(r => {
      html += `<div><p class="meta"><strong>${esc(r.interaction_class)}</strong>: ${show(r.source_interactions)} source interactions, ${show(r.eligible_unmasked)} eligible</p>
        ${barRow("Seed (Rfam)", r.rfam_preserved_eligible, r.eligible_unmasked, "b-rfam")}
        ${barRow("STAR3D forward", r.star3d_forward_preserved_eligible, r.eligible_unmasked, "b-star")}
        ${barRow("STAR3D reverse", r.star3d_reverse_preserved_eligible, r.eligible_unmasked, "b-star")}</div>`;
    });
    html += "</div>";
  } else html += `<p class="unavail">Interaction summary unavailable for this pair.</p>`;
  return html + "</div>";
}

function groupBy(rows) {
  const m = new Map();
  rows.forEach(g => { if (!m.has(g.pair_id)) m.set(g.pair_id, []); m.get(g.pair_id).push(g); });
  return m;
}

function renderResults(D) {
  const draw = () => {
    const t = $("tier-filter").value;
    const m = groupBy(D.pair_summary.rows);
    const ordered = [...m.entries()].sort((a, b) => (a[1][0].tier === "primary" ? 0 : 1) - (b[1][0].tier === "primary" ? 0 : 1));
    let html = `<p class="meta">Unit: residue of the source row; source: <code>${esc(D.pair_summary.source)}</code>; ${esc(D.pair_summary.note)}.</p>`;
    ordered.forEach(([pid, gs]) => {
      const tier = gs[0].tier;
      if (t === "primary" && tier !== "primary") return;
      if (t === "exploratory" && tier === "primary") return;
      html += pairCard(pid, gs, D);
    });
    $("dev-results").innerHTML = html;
  };
  $("tier-filter").addEventListener("input", draw);
  $("side-filter").addEventListener("input", draw);
  draw();
  const np = D.new_pair_summary;
  if (!np.available) $("new-results").innerHTML = `<p class="unavail">No prospective comparisons were run: the selection frozen before any STAR3D run is empty because none of the newly screened families met all primary criteria (see Dataset &rarr; screening table and <code>review/v3_screening/frozen_selection_v3.json</code>). Results are unavailable, not zero.</p>`;
  else {
    const m = groupBy(np.rows);
    $("new-results").innerHTML = `<p class="notice">Prospective pairs: exploratory until reviewed.</p>` + [...m.entries()].map(([pid, gs]) => pairCard(pid, gs, D)).join("");
  }
  $("regions-table").innerHTML = table(D.regions);
}

function renderCase(D) {
  const C = D.candidate_7rex;
  const fig = (D.figures.figures || []).find(f => /6VUI_7REX_P1/.test(f.file));
  $("case-figure").innerHTML = fig ? `<img src="${esc(fig.file)}" alt="Helix P1 of 6VUI and 7REX superposed, showing seed and STAR3D partners"><figcaption>P1 helix, 6VUI vs 7REX. Source: <code>${esc(fig.source)}</code></figcaption>` : `<p class="unavail">Figure unavailable.</p>`;

  const A = C.adjustment_summary;
  if (!A.available) $("adj-summary").innerHTML = `<p class="unavail">Unavailable.</p>`;
  else {
    const by = groupBy(A.rows);
    let html = `<p class="meta"><span class="tag exploratory">exploratory</span> "Adjusted" = agent-constructed shifted row. Source: <code>${esc(A.source)}</code></p><div class="classgrid">`;
    by.forEach((rows, pid) => {
      html += `<div class="card"><h4>${esc(pid)}</h4>`;
      rows.forEach(r => {
        html += `<p class="meta"><strong>${esc(r.interaction_class)}</strong> &middot; eligible (same set): ${show(r.eligible_same_set)}</p>
          ${barRow("Seed row", r.rfam_preserved, r.eligible_same_set, "b-rfam")}
          ${barRow("STAR3D", r.star3d_forward_preserved, r.eligible_same_set, "b-star")}
          ${barRow("Adjusted row", r.adjusted_preserved, r.eligible_same_set, "b-adj")}`;
      });
      html += "</div>";
    });
    $("adj-summary").innerHTML = html + "</div>";
  }
  $("corr-table").innerHTML = table(C.correspondence);
  $("counts-table").innerHTML = C.counts.available ? table(C.counts) : "";
  $("methoddiff-table").innerHTML = table(D.method_differences);
  $("rows-table").innerHTML = table(D.rf00522_rows);

  const V = C.validation;
  if (!V.available) $("adj-validation").innerHTML = `<p class="unavail">Unavailable.</p>`;
  else {
    const d = V.data;
    const yn = b => b === true ? "<strong>yes</strong>" : b === false ? "<strong>NO</strong>" : show(b);
    const list = a => Array.isArray(a) ? (a.length ? a.map(esc).join(", ") : "none") : show(a);
    $("adj-validation").innerHTML = `<div class="tablewrap"><table><tbody>
      <tr><th scope="row">Nucleotides preserved</th><td>${yn(d.nucleotides_preserved)}</td></tr>
      <tr><th scope="row">Residue order preserved</th><td>${yn(d.order_preserved)}</td></tr>
      <tr><th scope="row">Alignment width unchanged</th><td>${yn(d.width_unchanged)}</td></tr>
      <tr><th scope="row">Mapping one-to-one</th><td>${yn(d.mapping_one_to_one)}</td></tr>
      <tr><th scope="row">Interactions lost by adjustment</th><td>${list(d.interactions_lost_by_adjustment)}</td></tr>
      <tr><th scope="row">Columns changed</th><td>${list(d.columns_changed)}</td></tr>
      <tr><th scope="row">P1 pairs implied by consensus (original row)</th><td>${list(d.sscons_P1_pairs_original)}</td></tr>
      <tr><th scope="row">P1 pairs implied by consensus (adjusted row)</th><td>${list(d.sscons_P1_pairs_adjusted)}</td></tr>
      <tr><th scope="row">Original row</th><td><code>${show(d.original_row)}</code></td></tr>
      <tr><th scope="row">Adjusted row</th><td><code>${show(d.adjusted_row)}</code></td></tr>
      </tbody></table></div><p class="meta">Source: <code>${esc(V.source)}</code></p>`;
  }
  $("case-regions").innerHTML = (C.regions || []).map(r => `<div class="card"><h4>${esc(r.region_id)} ${tierTag(r.tier)}</h4>
    <p class="meta">correspondence disagreements: ${show(r.n_correspondence_disagreements)} residues; coverage differences: ${show(r.n_coverage_differences)}; seed elements: ${show(r.seed_elements)}</p>
    <p><strong>Classification:</strong> ${show(r.classification)}</p>
    <details><summary>Interpretation notes</summary><p>${show(r.interpretation)}</p><p class="meta">${show(r.interpretation_source)}</p></details></div>`).join("") || `<p class="unavail">unavailable</p>`;

  $("anchor-fits").innerHTML = (C.anchor_fits || []).map(a => `<details><summary>${esc(a.file.split("/").pop())} &middot; rule ${show(a.rule)} &middot; ${show(a.n_anchors)} anchors &middot; fit RMSD ${show(a.fit_rmsd_A)} &Aring;</summary>
    <p class="meta">${esc(a.header)}</p>${table({ columns: a.columns, rows: a.rows, source: a.file })}</details>`).join("") || `<p class="unavail">unavailable</p>`;
  const anchorFigs = (D.figures.figures || []).filter(f => /anchorfit/.test(f.file));
  if (anchorFigs.length) $("anchor-fits").innerHTML += `<div class="grid2">${anchorFigs.map(f => `<figure><img src="${esc(f.file)}" alt="Anchor-fit distance plot ${esc(f.file)}" loading="lazy"><figcaption>${esc(f.source)}</figcaption></figure>`).join("")}</div>`;
  const other = (D.figures.figures || []).filter(f => !/anchorfit|6VUI_7REX_P1/.test(f.file));
  if (other.length) $("anchor-fits").innerHTML += `<h3>Session figures</h3><div class="grid2">${other.map(f => `<figure><img src="${esc(f.file)}" alt="${esc(f.file)}" loading="lazy"><figcaption>${esc(f.source)}</figcaption></figure>`).join("")}</div>`;
}

function renderValidation(D) {
  const R = D.run_status;
  const sc = Object.entries(R.current_status_counts).map(([k, v]) => `<li><strong>${esc(k)}</strong>: ${show(v)} of ${show(R.current_rows)} steps</li>`).join("");
  $("run-status").innerHTML = `<ul>${sc}</ul><p class="meta">Historical attempt rows excluded from denominators: ${show(R.historical_attempt_rows_excluded)}. Source: <code>${esc(R.source)}</code></p>`;
  const rep = D.pair_summary.rows.map(g => ({ pair_id: g.pair_id, direction: g.direction, tier: g.tier, completed: `${g.completed_runs} / ${g.runs}`, identical_across_replicates: g.replicates_identical, distinct_outputs: g.distinct_outputs }));
  $("replicates").innerHTML = table({ rows: rep, source: "results/replicate_consistency.tsv + results/pair_summary.tsv" });
  $("tests-table").innerHTML = table(D.test_results);
  $("checks-table").innerHTML = table(D.validation_checks);
  $("results-status-table").innerHTML = table(D.results_status);
  $("req-table").innerHTML = table(D.requirements_status);
  $("fresh-table").innerHTML = table(D.fresh_repro_other4);
}

function renderDownloads(D) {
  $("downloads-list").innerHTML = `<ul class="dl">${D.downloads.downloads.map(d => d.href
    ? `<li><a href="${esc(d.href)}" download>${esc(d.label)}</a> &mdash; ${esc(d.description || "")}</li>`
    : `<li>${esc(d.label)} &mdash; <span class="unavail">unavailable</span></li>`).join("")}</ul>`;
}

function renderFooter(D) {
  const M = D.export_manifest, p = M.provenance || {};
  $("provenance").innerHTML = `Provenance: Rfam ${show(p.rfam_release)} <code>${show(p.reference_source)}</code> (sha256 <code>${show(p.seed_sha256)}</code>) &middot;
    STAR3D v${show(p.star3d_version)} original (tarball sha256 <code>${show(p.star3d_sha256)}</code>) &middot;
    FR3D-python commit <code>${show(p.fr3d_commit)}</code> &middot; cohort ${show(p.cohort_version)} &middot;
    git commit <code>${show(M.git_commit)}</code> (worktree ${show(M.git_worktree)}) &middot; data generated ${show(M.generated_utc)} by <code>${show(M.generator)}</code> from ${M.sources.length} source files
    (<a href="data/export_manifest.json">manifest with checksums</a>). Unavailable optional inputs at build: ${M.unavailable_optional_inputs.length}.`;
}

async function main() {
  const D = {};
  try {
    await Promise.all(FILES.map(async f => {
      const r = await fetch(`data/${f}.json`);
      if (!r.ok) throw new Error(`data/${f}.json: HTTP ${r.status}`);
      D[f] = await r.json();
    }));
  } catch (e) {
    const el = $("load-error");
    el.hidden = false;
    el.textContent = `Could not load data (${e.message}). Serve this folder over HTTP (python -m http.server) and regenerate with scripts/export_site_data.py.`;
    return;
  }
  const steps = [renderKpis, renderFunnel, renderFamilies, renderDataset, renderResults, renderCase, renderValidation, renderDownloads, renderFooter];
  steps.forEach(fn => { try { fn(D); } catch (e) { console.error(fn.name, e); } });
}
main();
