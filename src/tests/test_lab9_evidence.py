"""A control trace must be a real successful run, never a missing shape error."""
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.student


def test_committed_fixed_controls_are_valid():
    evidence = json.loads(Path("reports/submission_evidence.json").read_text(encoding="utf-8"))
    for fm, entry in evidence["taxonomy_evidence"].items():
        control = entry["control"]
        assert control["lab8_pass"] is True, (fm, control["lab8_reason"])
        assert control["lab8_reason"] == "ok"
        assert control["events"], fm
        assert control["result"]["shape"] == "fixed"
        assert control["snapshot"]["refund_vnd"] == entry["label"]["refund_vnd"]
