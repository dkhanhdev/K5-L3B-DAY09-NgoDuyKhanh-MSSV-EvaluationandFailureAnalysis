"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("orchestrator", claim_id, seed))

    def end(
        status: str,
        proposal_amount: int = 0,
        error_reason: str | None = None,
    ) -> RunResult:
        trace.add(
            "decision",
            {"status": status, "proposal_amount": int(proposal_amount)},
        )
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    # Read only the sanitized claim interface. The ticket is untrusted and is
    # deliberately not copied into the handoff, trace, or any model prompt.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim.get("found"):
        return end("failed", error_reason="unknown_claim")
    if not claim.get("order_id"):
        return end("needs_info", error_reason="missing_order_id")

    handoff = make_handoff(
        request_id=f"{trace.run_id}-investigation",
        claim_id=claim_id,
        task="verify_order_scope_and_compute_entitlement",
        facts={},
        allowed_tools=[
            "lookup_order",
            "lookup_policy",
            "lookup_refund_history",
            "compute_compensation",
        ],
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(
        conn,
        budget,
        handoff,
        principal_id=claim["principal_id"],
    )
    tools = investigated.get("tools") or {}
    order_view = tools.get("lookup_order") or {}
    policy_view = tools.get("lookup_policy") or {}
    refund_history = tools.get("lookup_refund_history") or {}
    trace.add(
        "investigator",
        {
            "claim_view": safe_dump(investigated.get("claim_view") or {}),
            "order_visible": bool(order_view.get("visible")),
            "order_reason": order_view.get("reason"),
            "policy_count": len(policy_view.get("policies") or []),
            "refund_history": {
                key: refund_history[key]
                for key in ("visible", "reason", "refund_count", "refunded_vnd")
                if key in refund_history
            },
        },
    )
    if not order_view.get("visible"):
        return end("escalated", error_reason=order_view.get("reason"))

    quote = tools.get("compute_compensation") or {}
    proposal = int(quote.get("amount_vnd") or 0)
    trace.add(
        "quote",
        {
            key: quote[key]
            for key in ("amount_vnd", "reason", "clause_ids", "parts")
            if key in quote
        },
    )
    if proposal <= 0:
        return end("denied", error_reason=quote.get("reason") or "no_entitlement")

    # The host owns approval, per-order caps, idempotency and the ledger. Pass
    # the full entitlement quote and let deterministic crash injection escape.
    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return end(status, proposal, outcome["reason"])
    return end("resolved", proposal)
