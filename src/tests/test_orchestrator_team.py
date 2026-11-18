"""Member 3: Orchestrator handoff, privacy, host gate, and recovery."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.handoff import ALLOWED_FIELDS, FACT_KEYS, READONLY_TOOLS, WRITE_TOOLS, make_handoff
from lab8.runtime import ToolRejected, dispatch
from lab8.schemas import Budget
from lab8.shapes import orchestrator


def _trace(result) -> dict:
    return json.loads(Path(result.trace_path).read_text(encoding="utf-8"))


def _ledger_count(path, claim_id: str) -> int:
    conn = connect(path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()
        return int(row["n"])
    finally:
        conn.close()


def test_orchestrator_uses_sanitized_readonly_handoff_and_clean_trace(public_db, monkeypatch):
    captured = {}
    original = orchestrator.make_handoff

    def inspect_handoff(**kwargs):
        handoff = original(**kwargs)
        captured.update(handoff)
        return handoff

    monkeypatch.setattr(orchestrator, "make_handoff", inspect_handoff)
    result = orchestrator.run_claim("C-010", seed=11, store_path=str(public_db))

    conn = connect(public_db)
    try:
        claim = conn.execute(
            "SELECT ticket, parent_secret, raw_headers_json, order_id FROM claims WHERE claim_id = ?",
            ("C-010",),
        ).fetchone()
        order = conn.execute(
            "SELECT phone, address, internal_note, item_name FROM orders WHERE order_id = ?",
            (claim["order_id"],),
        ).fetchone()
        forbidden = [claim["ticket"], claim["parent_secret"], claim["raw_headers_json"], *order]
    finally:
        conn.close()

    trace = _trace(result)
    blobs = [
        json.dumps(captured, ensure_ascii=False),
        json.dumps(trace, ensure_ascii=False),
    ]
    assert result.status == "resolved"
    assert set(captured) == ALLOWED_FIELDS
    assert set(captured["facts"]) <= FACT_KEYS
    assert set(captured["allowed_tools"]) <= READONLY_TOOLS
    assert not (set(captured["allowed_tools"]) & WRITE_TOOLS)
    for blob in blobs:
        assert "parent_secret" not in blob
        assert "raw_headers" not in blob
        assert "principal_id" not in blob
        assert all(value not in blob for value in forbidden)


def test_investigator_registry_rejects_write_tools(public_db):
    conn = connect(public_db)
    try:
        with pytest.raises(ToolRejected):
            dispatch(
                conn,
                Budget(),
                "issue_refund",
                {"claim_id": "C-001", "proposed_vnd": 35000},
                worker=True,
            )
        with pytest.raises(ValueError):
            make_handoff(
                request_id="write-attempt",
                claim_id="C-001",
                task="write",
                facts={},
                allowed_tools=["append_audit"],
            )
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("claim_id", "expected_status"),
    [("UNKNOWN", "failed"), ("C-004", "needs_info")],
)
def test_early_returns_write_valid_trace(public_db, claim_id, expected_status):
    result = orchestrator.run_claim(claim_id, seed=11, store_path=str(public_db))
    trace = _trace(result)
    assert result.status == expected_status
    assert result.proposal_amount == 0
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)


def test_order_outside_principal_scope_escalates(public_db):
    result = orchestrator.run_claim("C-005", seed=11, store_path=str(public_db))
    assert result.status == "escalated"
    assert result.proposal_amount == 0
    assert result.refund_effects == []


def test_zero_quote_does_not_call_host_or_write_ledger(public_db, monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "issue_refund",
        lambda *args, **kwargs: pytest.fail("zero quote must not call issue_refund"),
    )
    result = orchestrator.run_claim("C-002", seed=11, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert _ledger_count(public_db, "C-002") == 0


def test_invalid_approval_is_denied_by_host(public_db, monkeypatch):
    calls = []
    original = orchestrator.issue_refund

    def inspect_host(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(orchestrator, "issue_refund", inspect_host)
    result = orchestrator.run_claim("C-007", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    try:
        denied = conn.execute(
            "SELECT COUNT(*) AS n FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
            ("C-007",),
        ).fetchone()["n"]
    finally:
        conn.close()
    assert len(calls) == 1
    assert calls[0][0][2] == 35000
    assert result.status == "denied"
    assert result.proposal_amount == 35000
    assert result.refund_effects == []
    assert denied == 1


def test_retry_is_idempotent(public_db):
    first = orchestrator.run_claim("C-011", seed=11, store_path=str(public_db))
    second = orchestrator.run_claim("C-011", seed=11, store_path=str(public_db))
    assert first.status == second.status == "resolved"
    assert len(second.refund_effects) == 1
    assert second.committed_audit_count == 1
    assert _ledger_count(public_db, "C-011") == 1


@pytest.mark.parametrize(
    "point",
    ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"],
)
def test_crash_windows_propagate_and_resume_once(public_db, point):
    with pytest.raises(InjectedCrash):
        orchestrator.run_claim(
            "C-001",
            seed=11,
            store_path=str(public_db),
            crash_at=point,
        )
    resumed = orchestrator.run_claim("C-001", seed=11, store_path=str(public_db))
    assert resumed.status == "resolved"
    assert len(resumed.refund_effects) == 1
    assert resumed.committed_audit_count == 1
    assert _ledger_count(public_db, "C-001") == 1


def test_proposal_keeps_full_quote_when_host_applies_order_cap(public_db):
    result = orchestrator.run_claim("C-014", seed=11, store_path=str(public_db))
    assert result.status == "resolved"
    assert result.proposal_amount == 150000
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 120000
    assert result.committed_audit_count == 1
