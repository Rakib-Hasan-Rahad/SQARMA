"""INVENTED TEST DATA ONLY: STAR3D .aln parser (format from STAR3D.java output code)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import star3d  # noqa: E402

ALN = """#STAR3d alignment for x1a_A and y2b_B (2026/10/09 00:00:00)
############
#Parameters#
############
#RMSD cutoff: 4.0A
#Minimum stack size: 3
#Gap open penalty: -5.0
#Gap extension penalty: -2.0
#Match score: 3.0
#Mismatch score: 0.0
#########
#Results#
#########
#Aligned nucleotide: 4
#Alignment RMSD: 1.23A
#Nucleotide mapping:
A:1<->B:10
A:2<->B:11A
A:-3<->B:12
7:100B<->B:13
"""


def test_parse_mapping_with_icode_negative_and_digit_chain(tmp_path):
    p = tmp_path / "t.aln"
    p.write_text(ALN)
    r = star3d.parse_aln(str(p))
    assert r["aligned_n"] == 4 and r["rmsd"] == 1.23 and not r["bad_lines"]
    assert r["pairs"][1] == (("A", 2, ""), ("B", 11, "A"))
    assert r["pairs"][2] == (("A", -3, ""), ("B", 12, ""))
    assert r["pairs"][3] == (("7", 100, "B"), ("B", 13, ""))
    assert r["parameters"]["RMSD cutoff"] == "4.0A"


def test_declared_count_mismatch_flagged(tmp_path):
    p = tmp_path / "t.aln"
    p.write_text(ALN.replace("#Aligned nucleotide: 4", "#Aligned nucleotide: 5"))
    assert star3d.parse_aln(str(p))["bad_lines"]
