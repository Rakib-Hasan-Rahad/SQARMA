"""v4: a partial (subset) rerun must be refused before it can overwrite the complete global tables."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import compare  # noqa: E402
import interactions  # noqa: E402
import reference  # noqa: E402


@pytest.mark.parametrize("mod", [compare, interactions, reference])
def test_subset_run_refused_before_any_write(mod, monkeypatch, tmp_path):
    writes = []
    monkeypatch.setattr(mod, "P", lambda *a: (writes.append(a), str(tmp_path / "x"))[1])
    with pytest.raises(SystemExit, match="subset runs"):
        mod.main(["RF00522__3FU2_A__6VUI_A"])
    assert writes == [], "no table path may be touched before the refusal"
