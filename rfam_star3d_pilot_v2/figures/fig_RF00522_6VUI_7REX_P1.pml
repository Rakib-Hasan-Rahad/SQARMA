# Reproducible PyMOL script: RF00522 6VUI_A (T. tengcongensis, grey) vs 7REX_A (C. antarcticum, teal).
# Fit: C1' atoms of the 16 residue pairs on which the standard seed and STAR3D AGREE
# (6VUI 1-6 <-> 7REX 1-6; 6VUI 24-33 <-> 7REX 25-34) — neither disputed mapping is used for the fit.
# Numbering = author numbering of the aligner input files (== mmCIF label for these two chains).
# Run: pymol -cq figures/fig_RF00522_6VUI_7REX_P1.pml   (from the study root)
load runs/_inputs/6vuia.pdb, t6vui
load runs/_inputs/7rexa.pdb, c7rex
pair_fit c7rex///1-6/C1' + c7rex///25-34/C1', t6vui///1-6/C1' + t6vui///24-33/C1'
hide everything
set cartoon_ring_mode, 3
show cartoon
color grey70, t6vui
color teal, c7rex
show sticks, (t6vui///1-5+15-20) and not name OP1+OP2+P
show sticks, (c7rex///1-5+16-22) and not name OP1+OP2+P
color grey40, t6vui and elem C
color deepteal, c7rex and elem C
# seed partners of 6VUI 16-20 are 7REX 17-21 (red dashes), STAR3D partners are 7REX 18-22 (blue dashes)
distance seed_C16, t6vui///16/C1', c7rex///17/C1'
distance s3d_C16, t6vui///16/C1', c7rex///18/C1'
color red, seed_*
color blue, s3d_*
set dash_width, 3
label t6vui///16/C1', "6VUI C16 + 7REX C18 (STAR3D)"
label c7rex///17/C1', "7REX C17 (seed)"
set label_position, [0, -3, 6], c7rex
set label_position, [0, 3, 6], t6vui
set label_size, 17
set label_outline_color, white
set float_labels, 1
set label_font_id, 7
set cartoon_transparency, 0.55
set label_color, black
bg_color white
select focus, (t6vui and resi 1-5+15-20) or (c7rex and resi 1-5+16-22)
orient focus
zoom focus, 9
clip slab, 200
set label_distance_digits, 1
set dash_gap, 0.25
set dash_radius, 0.12
set dash_color, red, seed_*
set dash_color, blue, s3d_*
set ray_opaque_background, 1
png figures/fig_RF00522_6VUI_7REX_P1.png, width=1600, height=1200, dpi=200, ray=1
save figures/fig_RF00522_6VUI_7REX_P1.pse
