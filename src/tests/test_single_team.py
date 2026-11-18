"""Member 2: recovery, bounded reads and trace privacy."""
import json
import pytest
from lab8.durability import InjectedCrash
from lab8.shapes import single


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_single_recovers_at_each_crash_window(public_db, point):
    with pytest.raises(InjectedCrash):
        single.run_claim("C-001", seed=11, store_path=str(public_db), crash_at=point)
    result = single.run_claim("C-001", seed=11, store_path=str(public_db))
    retry = single.run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == retry.status == "resolved"
    assert len(retry.refund_effects) == retry.committed_audit_count == 1
    assert retry.refund_effects[0]["amount_vnd"] == 35000


def test_single_read_loop_is_bounded_and_counted(public_db, monkeypatch):
    original = single.run_react
    def inspect_loop(*args, **kwargs):
        assert kwargs["max_steps"] == 8
        assert kwargs["worker"] is True
        return original(*args, **kwargs)
    monkeypatch.setattr(single, "run_react", inspect_loop)
    result = single.run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.model_calls == 2
    assert result.status == "resolved"


def test_single_step_cap_does_not_write(public_db, monkeypatch):
    monkeypatch.setattr(single, "run_react", lambda *a, **k: {
        "stopped": "step_cap", "final": {"status": "failed", "error_reason": "step_cap"}})
    result = single.run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "step_cap"
    assert result.refund_effects == []


def test_single_unknown_claim_writes_valid_trace(public_db):
    result = single.run_claim("UNKNOWN", seed=11, store_path=str(public_db))
    trace = json.loads(__import__("pathlib").Path(result.trace_path).read_text(encoding="utf-8"))
    assert result.status == "failed"
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    assert "CANARY_SECRET" not in json.dumps(trace)
