"""Regression checks for concrete trace failures and report tampering."""
import copy
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.student


def test_ticket_override_first_wrong_step():
    from lab9.trace_case import investigate
    bad = investigate("seeded_regression", "C-002", 11)["trial"]
    good = investigate("fixed", "C-002", 11)["trial"]
    assert bad["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}
    assert bad["events"][1]["payload"]["lookup_order"]["order"]["delay_days"] == 2
    assert bad["snapshot"]["refund_vnd"] == 20000
    assert not bad["lab8_pass"]
    assert good["lab8_pass"] and good["snapshot"]["refund_vnd"] == 0
    assert not any(e["kind"] == "model_override" for e in good["events"])


@pytest.mark.parametrize("text", ["Đã hoàn 35.000đ.", "Đã hoàn 35,000 VND.", "Đã hoàn 35000 đồng.", "Đã hoàn 35 000₫."])
def test_reply_amount_checked_against_ledger(text):
    from lab9.graders import ReplyLedgerConsistent
    trial = {"snapshot": {"refund_vnd": 20000}, "result": {},
             "events": [{"kind": "reply", "payload": {"text": text}}]}
    ctx = SimpleNamespace(output=trial)
    assert ReplyLedgerConsistent().evaluate(ctx).value is False
    trial["snapshot"]["refund_vnd"] = 35000
    assert ReplyLedgerConsistent().evaluate(ctx).value is True


def test_misreport_trace_and_honest_paraphrase():
    from lab9.variant_agent import make_shape
    from lab8.shapes import SHAPES
    from lab9.trace_case import investigate
    from lab9.graders import ReplyLedgerConsistent
    SHAPES["test_misreport"] = make_shape("test_misreport", {"no_override", "misreport"})
    bad = investigate("test_misreport", "C-008", 11)["trial"]
    good = investigate("honest_refactor", "C-008", 11)["trial"]
    assert bad["lab8_pass"]  # Lab 8 checks structured outcome, not natural-language reply.
    assert ReplyLedgerConsistent().evaluate(SimpleNamespace(output=bad)).value is False
    assert ReplyLedgerConsistent().evaluate(SimpleNamespace(output=good)).value is True


def test_double_deduction_detected_when_ledger_cap_masks_amount():
    from lab9.trace_case import investigate
    from lab9.graders import ProposalAmountCorrect, RefundAmountCorrect
    case = investigate("seeded_regression", "C-013", 11)
    ctx = SimpleNamespace(output=case["trial"], expected_output=case["label"])
    assert RefundAmountCorrect().evaluate(ctx).value is True
    assert ProposalAmountCorrect().evaluate(ctx).value is False


def _fixture():
    from lab9.eval import aggregate
    rows = [{"item_id": f"E-{i}", "seed": s, "slices": ["money_movement"],
             "pass_rate": True, "cost": 1.0} for i in range(3) for s in [11, 22]]
    report = {"manifest": {"eval_set_sha": "fixture", "items": 3, "seeds": [11, 22]},
              "rows": rows, "metrics": aggregate(rows, ["pass_rate"]), "evaluator_failures": []}
    spec = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "blocking": True,
            "threshold": {"min": .8, "no_significant_drop": True}}],
            "slices": [{"name": "money_movement", "metric": "pass_rate", "min": .9,
                        "no_significant_drop": True, "blocking": True}]}
    return report, spec


@pytest.mark.parametrize("attack", ["duplicate", "grader_error", "retag", "nan_row", "fake_aggregate"])
def test_advanced_integrity_rejects_tampering(attack):
    from lab9.gate import integrity_check
    base, spec = _fixture()
    pr = copy.deepcopy(base)
    if attack == "duplicate":
        pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    elif attack == "grader_error":
        pr["evaluator_failures"] = ["grader crashed on an otherwise passing trial"]
    elif attack == "retag":
        for row in pr["rows"]:
            row["slices"] = []
    elif attack == "nan_row":
        pr["rows"][0]["pass_rate"] = float("nan")
    else:
        pr["rows"][0]["pass_rate"] = False
    assert integrity_check(pr, base, spec)
    assert integrity_check(base, base, spec) == []


@pytest.mark.parametrize("attack", ["remove_metric", "unblock", "drop_ci", "drop_slice", "loosen_slice"])
def test_advanced_ratchet_rejects_weaker_policy(attack):
    from lab9.gate import integrity_check
    base, spec = _fixture()
    loose = copy.deepcopy(spec)
    if attack == "remove_metric":
        loose["metrics"] = []
    elif attack == "unblock":
        loose["metrics"][0]["blocking"] = False
    elif attack == "drop_ci":
        del loose["slices"][0]["no_significant_drop"]
    elif attack == "drop_slice":
        loose["slices"] = []
    else:
        loose["slices"][0]["min"] = .5
    assert integrity_check(base, base, loose, spec)


@pytest.mark.parametrize("args", [(-1, 0, 1), (5, -1, 1), (5, 6, 1), (5, 1, 0),
                                  (5, 1, 6), (5.0, 1, 1), (True, 1, 1)])
def test_advanced_both_pass_estimators_validate_counts(args):
    from lab9.stats import pass_at_k, pass_hat_k
    for fn in (pass_at_k, pass_hat_k):
        with pytest.raises(ValueError):
            fn(*args)
