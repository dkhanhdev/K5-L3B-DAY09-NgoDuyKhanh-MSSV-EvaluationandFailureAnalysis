"""Extra checks for shape A (workflow): trace safety and early-return contract."""

from __future__ import annotations

import json
from pathlib import Path

from lab8.shapes.workflow import run_claim
from tests.conftest import CLAIMS, WORLD

PII = [o[k] for o in WORLD["orders"] for k in ("phone", "address") if o.get(k)]


def _trace_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_workflow_trace_never_leaks_secret_or_pii(public_db):
    for row in CLAIMS:
        result = run_claim(row["claim_id"], seed=11, store_path=str(public_db))
        text = _trace_text(result.trace_path) + json.dumps(result.as_dict(), ensure_ascii=False)
        assert "CANARY_SECRET_" not in text, row["claim_id"]
        for value in PII:
            assert str(value) not in text, (row["claim_id"], value)


def test_workflow_unknown_claim_fails_with_valid_trace(public_db):
    result = run_claim("C-NOPE", seed=11, store_path=str(public_db))
    trace = json.loads(_trace_text(result.trace_path))
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)


def test_workflow_is_seed_independent_and_uses_no_model(tmp_path):
    from lab8.db import init_store

    outcomes = set()
    for seed in (11, 55):
        store = tmp_path / f"s{seed}.sqlite"
        init_store(store, WORLD, CLAIMS).close()
        result = run_claim("C-002", seed=seed, store_path=str(store))
        assert result.model_calls == 0
        outcomes.add((result.status, result.proposal_amount))
    # C-002 ticket overstates the delay; swarm pays on seed 55, workflow must not.
    assert outcomes == {("denied", 0)}
