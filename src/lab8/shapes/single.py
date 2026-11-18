"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, compute_compensation, tool_cost
from lab8.trace import Trace


def run_claim(claim_id: str, *, seed: int, store_path: str,
              crash_at: str | None = None) -> RunResult:
    conn = connect(store_path)
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))

    def end(status, amount=0, reason=None):
        trace.add("decision", {"status": status, "proposal_amount": amount})
        return finish(conn, shape="single", claim_id=claim_id, seed=seed,
                      status=status, proposal_amount=amount, budget=budget,
                      trace=trace, error_reason=reason)

    try:
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        # The ticket is untrusted data. Never copy it into prompts or traces.
        if not claim["found"]:
            return end("failed", reason="unknown_claim")
        if not claim.get("order_id"):
            return end("needs_info", reason="missing_order_id")

        def decide(observation):
            # MockLLM has no structured tool-call API: the adapter maps the
            # observed stage to a read action, accounting for every model turn.
            stage = observation.get("last_tool", "start")
            complete(budget, seed=seed, purpose="decide", prompt=f"stage={stage}")
            if stage == "start":
                return {"tool": "lookup_order", "args": {
                    "order_id": claim["order_id"], "principal_id": claim["principal_id"]}}
            if stage == "lookup_order":
                view = observation["last_result"]
                if not view["visible"]:
                    return {"final": {"status": "escalated", "reason": view["reason"]}}
                return {"final": {"order": view["order"]}}
            return {"final": {"status": "failed", "reason": "unexpected_observation"}}

        result = run_react(conn, budget, observation={"claim": {
            "claim_id": claim_id, "order_id": claim["order_id"]}},
            decide=decide, max_steps=8, worker=True)
        trace.add("react", {"stopped": result["stopped"]})
        final = result["final"]
        if "order" not in final:
            return end(final.get("status", "failed"),
                       reason=final.get("reason", final.get("error_reason")))
        # Money and writes are controlled by code after the read-only loop.
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, final["order"])
        amount = int(quote["amount_vnd"])
        trace.add("quote", quote)
        if amount <= 0:
            return end("denied", reason=quote.get("reason"))
        outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
        if not outcome["ok"]:
            return end("failed" if outcome["conflict"] else "denied",
                       amount, outcome["reason"])
        return end("resolved", amount)
    finally:
        conn.close()
