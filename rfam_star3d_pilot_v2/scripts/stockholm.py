"""Strict Stockholm 1.0 parser for Rfam seed files.

Sequence rows and #=GR / #=GC annotation rows are concatenated across interleaved
blocks. Annotation rows are never treated as sequences. Malformed records raise
StockholmError with the record accession and line number instead of being dropped.
"""
import gzip
import re
from collections import OrderedDict

SEQ_ALPHABET = set("ACGUTRYKMSWBDHVNacgutrykmswbdhvn-.")


class StockholmError(ValueError):
    pass


class Alignment:
    def __init__(self):
        self.gf = OrderedDict()      # tag -> list of values (in order)
        self.gs = OrderedDict()      # seqname -> tag -> list
        self.seqs = OrderedDict()    # seqname -> aligned string
        self.gr = OrderedDict()      # seqname -> feature -> aligned string
        self.gc = OrderedDict()      # feature -> aligned string
        self.start_line = None
        self.seq_lines = OrderedDict()  # seqname -> list of 1-based line numbers in the decompressed file

    @property
    def acc(self):
        return self.gf.get("AC", [""])[0].strip()

    @property
    def id(self):
        return self.gf.get("ID", [""])[0].strip()

    @property
    def width(self):
        return len(next(iter(self.seqs.values()))) if self.seqs else 0

    def ungapped(self, name):
        return re.sub(r"[-.]", "", self.seqs[name])

    def gr_by_feature(self):
        """feature -> list of seqnames carrying it (e.g. '2GIS_A_SS' -> [URS...])."""
        out = {}
        for name, feats in self.gr.items():
            for f in feats:
                out.setdefault(f, []).append(name)
        return out


DECODE_FALLBACKS = []   # (path, lineno) of lines that were not valid UTF-8 (decoded as Latin-1)


def _open(path):
    fh = gzip.open(path, "rb") if str(path).endswith(".gz") else open(path, "rb")
    for lineno, b in enumerate(fh, 1):
        try:
            yield b.decode("utf-8")
        except UnicodeDecodeError:
            DECODE_FALLBACKS.append((str(path), lineno))
            yield b.decode("latin-1")
    fh.close()


def parse(path, only=None):
    """Yield Alignment objects. `only`: optional set of accessions to keep (others are
    still syntax-checked lightly but not stored)."""
    aln = None
    if True:
        for lineno, raw in enumerate(_open(path), 1):
            line = raw.rstrip("\n")
            if line.startswith("# STOCKHOLM"):
                if aln is not None:
                    raise StockholmError(f"line {lineno}: new header before '//' terminator")
                aln = Alignment()
                aln.start_line = lineno
                continue
            if aln is None:
                if line.strip():
                    raise StockholmError(f"line {lineno}: content outside a record")
                continue
            if line.startswith("//"):
                _validate(aln, lineno)
                if only is None or aln.acc in only:
                    yield aln
                aln = None
                continue
            if not line.strip():
                continue
            try:
                _consume(aln, line, lineno)
            except StockholmError as e:
                raise StockholmError(f"line {lineno} (record {aln.acc or '?'}): {e}") from None
    if aln is not None:
        raise StockholmError("file ended without '//' terminator")


def _consume(aln, line, lineno=None):
    if line.startswith("#=GF"):
        parts = line.split(None, 2)
        if len(parts) < 2:
            raise StockholmError("bad #=GF line")
        aln.gf.setdefault(parts[1], []).append(parts[2] if len(parts) > 2 else "")
    elif line.startswith("#=GS"):
        parts = line.split(None, 3)
        if len(parts) < 3:
            raise StockholmError("bad #=GS line")
        aln.gs.setdefault(parts[1], OrderedDict()).setdefault(parts[2], []).append(parts[3] if len(parts) > 3 else "")
    elif line.startswith("#=GR"):
        parts = line.split()
        if len(parts) != 4:
            raise StockholmError(f"#=GR line must have 4 fields, got {len(parts)}")
        _, name, feat, data = parts
        d = aln.gr.setdefault(name, OrderedDict())
        d[feat] = d.get(feat, "") + data
    elif line.startswith("#=GC"):
        parts = line.split()
        if len(parts) != 3:
            raise StockholmError(f"#=GC line must have 3 fields, got {len(parts)}")
        _, feat, data = parts
        aln.gc[feat] = aln.gc.get(feat, "") + data
    elif line.startswith("#"):
        return  # free comment
    else:
        parts = line.split()
        if len(parts) != 2:
            raise StockholmError(f"sequence line must have 2 fields, got {len(parts)}")
        name, data = parts
        aln.seqs[name] = aln.seqs.get(name, "") + data
        aln.seq_lines.setdefault(name, []).append(lineno)


def _validate(aln, lineno):
    where = f"record {aln.acc or '?'} ending line {lineno}"
    if not aln.seqs:
        raise StockholmError(f"{where}: no sequences")
    widths = {len(s) for s in aln.seqs.values()}
    if len(widths) != 1:
        raise StockholmError(f"{where}: unequal sequence lengths {sorted(widths)[:5]}")
    w = widths.pop()
    for name, s in aln.seqs.items():
        bad = set(s) - SEQ_ALPHABET
        if bad:
            raise StockholmError(f"{where}: unexpected characters {sorted(bad)} in {name}")
    for name, feats in aln.gr.items():
        if name not in aln.seqs:
            raise StockholmError(f"{where}: #=GR for unknown sequence {name}")
        for f, s in feats.items():
            if len(s) != w:
                raise StockholmError(f"{where}: #=GR {name} {f} length {len(s)} != {w}")
    for f, s in aln.gc.items():
        if len(s) != w:
            raise StockholmError(f"{where}: #=GC {f} length {len(s)} != {w}")
    for name in aln.gs:
        if name not in aln.seqs:
            raise StockholmError(f"{where}: #=GS for unknown sequence {name}")


NAME_RE = re.compile(r"^(?P<acc>[^/]+)/(?P<start>\d+)-(?P<end>\d+)$")


def split_name(name):
    """'URS000080DF35_32630/1-94' -> ('URS000080DF35_32630', 1, 94). Start>end means reverse strand."""
    m = NAME_RE.match(name)
    if not m:
        return name, None, None
    return m["acc"], int(m["start"]), int(m["end"])


def residue_columns(aligned):
    """List of alignment column indices (0-based) holding residues, in order."""
    return [i for i, c in enumerate(aligned) if c not in "-."]


def pairwise_correspondence(row_a, row_b):
    """Ordered list of (i, j) ungapped 0-based residue indices aligned in the same column."""
    ia = ib = 0
    out = []
    for ca, cb in zip(row_a, row_b):
        ga, gb = ca in "-.", cb in "-."
        if not ga and not gb:
            out.append((ia, ib))
        if not ga:
            ia += 1
        if not gb:
            ib += 1
    return out
