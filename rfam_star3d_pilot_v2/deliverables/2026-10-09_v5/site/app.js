/* v5 site renderer. Every number comes from data/*.json written by scripts/export_site_data.py.
   Missing values render as "unavailable", never 0. */
"use strict";
const FILES = ["kpis", "chains", "eligibility", "family_status", "pairs", "primary_outputs", "pair_summary", "interactions",
  "regions", "alignment_views", "region_evidence", "candidate", "validation", "figures", "downloads", "export_manifest"];
const UNAV = '<span class="unavail">unavailable</span>';
const $ = id => document.getElementById(id);
const esc = v => String(v).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const miss = v => v === undefined || v === null || v === "" || v === "NA";
const show = v => miss(v) ? UNAV : esc(v);
const num = v => (miss(v) || !/^-?\d+(\.\d+)?$/.test(String(v))) ? null : Number(v);

function table(p, opts = {}) {
  if (!p || p.available === false) return `<p class="unavail">unavailable${p && p.source ? ` (<code>${esc(p.source)}</code>)` : ""}</p>`;
  const cols = opts.columns || p.columns;
  const rows = opts.filter ? p.rows.filter(opts.filter) : p.rows;
  if (!rows.length) return '<p class="unavail">No rows.</p>';
  const head = cols.map(c => `<th scope="col">${esc(c)}</th>`).join("");
  const body = rows.map(r => "<tr>" + cols.map(c => {
    const v = r[c];
    if (c === "analysis_eligibility" || c === "eligibility") return `<td><span class="tag ${String(v).startsWith("accepted") ? "primary" : "exploratory"}">${show(v)}</span></td>`;
    const isNum = num(v) !== null, long = !miss(v) && String(v).length > 60;
    return `<td class="${isNum ? "num" : long ? "long" : ""}">${show(v)}</td>`;
  }).join("") + "</tr>").join("");
  return `<div class="tablewrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>
    <p class="meta">Source: <code>${esc(p.source)}</code> &middot; ${rows.length} row(s)</p>`;
}

function barRow(label, x, n, cls) {
  const a = num(x), b = num(n);
  let pct = 0, txt;
  if (a === null || b === null) txt = "unavailable";
  else if (b === 0) txt = "no eligible items";
  else { pct = 100 * a / b; txt = `${a} / ${b} (${pct.toFixed(0)}%)`; }
  return `<div class="barrow"><span>${esc(label)}</span><div class="bar" role="img" aria-label="${esc(label)}: ${esc(txt)}"><span class="${cls}" style="width:${pct}%"></span></div><span>${esc(txt)}</span></div>`;
}

function renderOverview(D) {
  const v = D.kpis.values;
  const items = [[v.families_with_accepted_pairs, "families with accepted pairs"], [v.accepted_pairs, "accepted pairs"],
    [v.accepted_structures_in_pairs, "structures in accepted pairs"], [v.verified_natural, "verified-natural chains"],
    [v.confirmed_engineered, "confirmed-engineered chains (excluded)"], [v.unresolved, "unresolved chains"],
    [v.chains_reviewed_under_policy, "chains reviewed under the policy"], [v.star3d_outputs_used, "STAR3D outputs used (one per pair)"]];
  $("kpis").innerHTML = items.map(([x, l]) => `<div class="kpi"><div class="v">${show(x)}</div><div class="l">${esc(l)}</div></div>`).join("");
}

function renderDataset(D) {
  const draw = () => {
    const f = $("chain-filter").value;
    $("chains-table").innerHTML = table(D.chains, {filter: r => !f || String(r.eligibility).startsWith(f)});
  };
  $("chain-filter").addEventListener("input", draw);
  draw();
  $("before-after").innerHTML = table(D.validation.before_after_natural);
  const c = D.family_status.counts;
  $("family-counts").innerHTML = `<ul>${Object.entries(c).map(([k, n]) => `<li><strong>${esc(k)}</strong>: ${show(n)} families</li>`).join("")}</ul>
    <p class="meta">Source: <code>${esc(D.family_status.source)}</code></p>`;
  $("family-table").innerHTML = table({available: true, source: D.family_status.source,
    columns: Object.keys(D.family_status.rows[0] || {}), rows: D.family_status.rows});
}

function renderResults(D) {
  const ints = D.interactions.rows;
  $("pair-cards").innerHTML = D.pair_summary.rows.map(p => {
    const pid = p.pair_id;
    const comp = ["same_partner", "different_partner", "rfam_only", "star3d_only", "neither"];
    const tot = comp.reduce((s, k) => s + (num(p[k]) || 0), 0);
    let h = `<div class="card"><h4>${esc(pid)}</h4><p class="meta">STAR3D output: <code>${esc(p.star3d_run_id)}</code>; RMSD ${show(p.star3d_rmsd)} &Aring;</p>`;
    h += barRow("same partner", p.same_partner, tot, "c-same") + barRow("different partner", p.different_partner, tot, "c-star") +
         barRow("seed only", p.rfam_only, tot, "b-rfam") + barRow("STAR3D only", p.star3d_only, tot, "b-rfam");
    h += `<p class="meta">Denominator: ${show(tot)} query-row residues. Assessable seed pairs reproduced by STAR3D: ${show(p.rfam_assessable_pairs_reproduced)} / ${show(p.rfam_pairs_structurally_assessable)}.</p>`;
    ["query", "target"].forEach(side => {
      const rows = ints.filter(r => r.pair_id === pid && r.source_side === side);
      if (!rows.length) return;
      h += `<p class="meta"><strong>${side === "query" ? "Query-RNA interactions (forward mapping)" : "Target-RNA interactions (same mapping inverted; no extra STAR3D run)"}</strong></p>`;
      rows.forEach(r => {
        h += `<p class="meta">${esc(r.interaction_class)} &middot; eligible ${show(r.eligible_unmasked)}</p>` +
          barRow("seed", r.rfam_preserved_eligible, r.eligible_unmasked, "b-rfam") + barRow("STAR3D", r.star3d_preserved_eligible, r.eligible_unmasked, "c-star");
      });
    });
    return h + "</div>";
  }).join("");
  const V = D.alignment_views;
  if (!V.available) $("views").innerHTML = `<p class="unavail">unavailable</p>`;
  else {
    const by = {};
    V.rows.forEach(r => (by[r.pair_id] = by[r.pair_id] || []).push(r));
    $("views").innerHTML = Object.entries(by).map(([pid, rs]) => `<h4>${esc(pid)}</h4><pre>${rs.map(r =>
      `${esc(r.method.padEnd(7))} ${esc(r.query.padEnd(7))} ${esc(r.query_gapped)}\n${"".padEnd(8)}${esc(r.target.padEnd(7))} ${esc(r.target_gapped)}\n${"".padEnd(8)}(${esc(r.n_correspondences)} correspondences)`).join("\n\n")}</pre>`).join("") +
      `<p class="meta">Lower-case = residue without coordinates. Source: <code>${esc(V.source)}</code></p>`;
  }
  $("regions-table").innerHTML = table(D.regions);
}

function renderCase(D) {
  const fig = D.figures.figures;
  $("case-figure").innerHTML = fig.length ? fig.map(f => `<img src="${esc(f.file)}" alt="${esc(f.file)}"><figcaption>Source: <code>${esc(f.source)}</code></figcaption>`).join("") : '<p class="unavail">unavailable</p>';
  $("cand-summary").innerHTML = table(D.candidate.adjustment_interaction_summary);
  $("cand-6vui").innerHTML = table(D.candidate.residue_evidence_RF00522__6VUI_A__7REX_A);
  $("cand-3fu2").innerHTML = table(D.candidate.residue_evidence_RF00522__3FU2_A__7REX_A);
  $("region-evidence").innerHTML = table(D.region_evidence);
}

function renderValidation(D) {
  $("primary-outputs").innerHTML = table(D.primary_outputs);
  $("tests").innerHTML = table(D.validation.tests);
  $("mutation").innerHTML = table(D.validation.mutation_check);
  $("single-run").innerHTML = table(D.validation.before_after_single_run);
  $("requirements").innerHTML = table(D.validation.requirements);
}

function renderDownloads(D) {
  $("downloads-list").innerHTML = `<ul class="dl">${D.downloads.downloads.map(d => d.href ? `<li><a href="${esc(d.href)}" download>${esc(d.label)}</a> &mdash; ${esc(d.description)}</li>` : `<li>${esc(d.label)} &mdash; ${UNAV}</li>`).join("")}</ul>`;
  const M = D.export_manifest, p = M.provenance;
  $("provenance").innerHTML = `Provenance: Rfam ${show(p.rfam_release)} Rfam.seed.gz (sha256 <code>${show(p.seed_sha256)}</code>) &middot; ${esc(p.star3d)} (tarball sha256 <code>${show(p.star3d_sha256)}</code>) &middot; ${esc(p.fr3d)} &middot; cohort ${esc(p.cohort)} &middot; git commit <code>${show(M.git_commit)}</code> (worktree ${esc(M.git_worktree)}) &middot; generated ${show(M.generated_utc)} from ${M.sources.length} sources (<a href="data/export_manifest.json">manifest</a>).`;
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
    el.textContent = `Could not load data (${e.message}). Serve this folder over HTTP (python -m http.server).`;
    return;
  }
  [renderOverview, renderDataset, renderResults, renderCase, renderValidation, renderDownloads].forEach(fn => {
    try { fn(D); } catch (e) { console.error(fn.name, e); }
  });
}
main();
