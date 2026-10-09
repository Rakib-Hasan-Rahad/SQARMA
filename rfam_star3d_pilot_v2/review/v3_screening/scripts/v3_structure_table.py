"""Build structure_facts.tsv from facts_raw*.jsonl + curated engineering/exact-source columns (dict below, from
exact_source_v3.tsv and the papers cited in screening_notes.md)."""
import json, csv, glob, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUR = {
 "3SD3_A": ("U25C (3WJ-site mutant; struct title) + Smu P1 GG/CC terminal-pair changes + P4 helix replaced by tetraloop (same construct as 4LVV; Trausch 2011 per PMC7981257 methods)", "NOT_found_exactly (AE014133.2; 9 diffs incl 25C>U, 59-61 P4 region, P1 termini)"),
 "3SUH_X": ("internal 14A,65C,85A vs natural U (noncanonical->WC, per v1 BLAST + this genome check) + terminal 1G,101C; PK strand-swap crystal artifact noted in PMC3935398/PMC7981257", "NOT_found_exactly (FP929059.1 & FP929044.1; 1G>C;14A>U;65C>U;85A>U;101C>G)"),
 "3SUX_X": ("same construct as 3SUH", "same sequence as 3SUH"), "3SUY_X": ("same construct as 3SUH", "same sequence as 3SUH"),
 "4LVV_A": ("P1 first two terminal pairs mutated to 5'GG/3'CC and P4 helix replaced with a tetraloop (PMC7981257 methods; consistent with genome diffs 1-2, 59-61, 87-89)", "NOT_found_exactly (AE014133.2 S. mutans UA159; 1G>A;2G>C;59G>C;ins U before 61;61G>A;87C>G;88C>U;89A>U)"),
 "6Q57_A": ("same sequence as 4LVV (engineered Smu construct)", "same sequence as 4LVV"), "7KD1_A": ("same sequence as 4LVV; paper states P1 GC mutations + P4 tetraloop", "same sequence as 4LVV"),
 "7QR3_C": ("P4 region 42-55 differs from human genomic (U1A-binding loop AUUGCAC; U1A protein co-crystallized); construct identical to human except pos 30; P1.1 replaced by crystal dimerization AC-like loop (abstract)", "chimp genome not checked (time); region 42-55 identical to engineered human construct"),
 "7QR3_D": ("crystal copy of 7QR3_C", "same sequence"),
 "7QR4_B": ("P4 region 42-55 not genomic (U1A-binding loop); struct_ref GB AL158040.14 covers only 1-41", "NOT_found_exactly (AL158040.14; 1-41 native, diffs 42-55)"),
 "2MF0_G": ("no engineering detected (exact genomic 1-72 fragment, SL1-SL4 only)", "exact_source_verified (CP003190.1 P. protegens CHA0, + strand 1388359)"),
 "2MF1_G": ("same as 2MF0 (alternative conformer entry)", "exact_source_verified (same sequence)"),
 "7YR6_A": ("one extra C at construct 61 vs PAO1 (unexplained; paper: full-length RsmZ in vitro transcribed; no sequence statement found)", "NOT_found_exactly (AE004091.2 PAO1 1 diff 61C>del; CP000438.1 PA14 2 diffs)"),
 "7YR7_A": ("same sequence as 7YR6", "same as 7YR6"),
 "4ZNP_A": ("internal non-genomic: ins/loop change ~26-28 (GGGAAACC), 51A>G; termini 1,72,73; papers inaccessible (captcha)", "NOT_found_exactly (AAWL01 T. carboxydivorans Nor1 WGS contigs; 7 diffs)"),
 "4ZNP_B": ("crystal copy of 4ZNP_A", "same sequence as 4ZNP_A"),
 "4XWF_A": ("internal non-genomic: 26-27 loop change + ~11-nt internal shortening at 43-47; termini 2,63; papers inaccessible (captcha)", "NOT_found_exactly (AAYI02 A. odontolyticus ATCC 17982 contigs; 15 diffs)"),
 "4XW7_A": ("same sequence as 4XWF_A", "same as 4XWF_A"),
 "4FRN_A": ("G12A,A14G,A31U,G42C,C62G + linker from AACY023653040/384-265 (PMC3518761 methods)", "NOT_found_exactly (AACY021350931.1; 6 diffs consistent with stated mutations)"),
 "4FRN_B": ("crystal copy of 4FRN_A", "same as 4FRN_A"),
 "4FRG_X": ("env8 AqCbl(dJ1/13,P13): P13 deleted/replaced (45-52) + 12 change (PMC3518761; exact check)", "NOT_found_exactly (AACY021350931.1; 8 diffs)"),
 "4FRG_B": ("crystal copy of 4FRG_X", "same as 4FRG_X"),
 "6LXD_D": ("apical loop CAUUGCACUCCGG non-natural (sequence inspection; U1A-type motif); 5' GGUGA extension outside row", "not checked"),
 "2QUS_A": ("G12A catalytic-core mutant (struct title)", "not checked"), "2QUW_B": ("G12A mutant, cleaved fragment (struct title)", "not checked"),
 "5DI2_A": ("artificially evolved hammerhead RzB (src_syn details)", "not applicable (artificial)"),
 "4L81_A": ("env87 deltaU92,deltaG93 (struct title)", "not checked"), "4OQU_A": ("env87 deltaU92 (struct title)", "not checked"),
 "6JQ5_A": ("capping loop GAAA (vs UUCG in 6JQ6); synthetic construct", "not checked"), "6JQ6_U": ("capping loop UUCG; synthetic construct", "not checked"),
}
cols = ["pdb", "chain_label", "chain_auth", "entity", "rfam_acc", "seed_row", "organism", "strain", "host", "method", "resolution", "n_models",
        "construct_length", "family_interval_label", "family_interval_auth", "observed_fraction", "missing_label_seq_ids", "modified_residues",
        "ligands", "engineering_found", "exact_source_verdict"]
out = []
for f in sorted(glob.glob(os.path.join(D, "facts_raw*.jsonl"))):
    for l in open(f):
        d = json.loads(l); fam, pdb, ch = d["spec"].split(":")
        org = "; ".join(filter(None, [x.get("organism_scientific") or ("NA(syn:" + (x.get("details") or "") + ")") for x in d["src_syn"]] +
                        [x["pdbx_gene_src_scientific_name"] for x in d["src_gen"]])) or "no annotation detected"
        host = "; ".join(filter(None, [x["pdbx_host_org_scientific_name"] for x in d["src_gen"]])) or "NA (in vitro / no annotation)"
        e, v = CUR.get(f"{pdb}_{ch}", ("not assessed beyond mmCIF (no struct_ref_seq_dif / pdbx_mutation annotation detected)", "not checked (time)"))
        out.append(dict(pdb=pdb, chain_label=",".join(d["label_asym"]), chain_auth=ch, entity=",".join(d["entity"]), rfam_acc=fam, seed_row=d["row"],
            organism=org, strain="NA", host=host, method=";".join(d["method"]), resolution=d["resolution"] or "NA", n_models=d["n_models"],
            construct_length=d["deposited_len"], family_interval_label="-".join(map(str, d.get("family_label") or [])),
            family_interval_auth="-".join(d.get("family_auth") or []), observed_fraction=d.get("observed_fraction"),
            missing_label_seq_ids=",".join(map(str, d.get("missing_label_in_family") or [])) or "none",
            modified_residues=",".join(f"{a}:{b}" for a, b in d.get("modified_in_family") or []) or "none",
            ligands=",".join(x[0] for x in d["ligands"] if x[0] != "HOH") or "none", engineering_found=e, exact_source_verdict=v))
w = csv.DictWriter(open(os.path.join(D, "structure_facts.tsv"), "w", newline=""), cols, delimiter="\t"); w.writeheader(); w.writerows(out)
print(len(out))
