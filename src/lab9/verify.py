"""Reproduce the full submission, preserving real command outputs and expected exit codes.

Run from src/: python -m lab9.verify
No reports are patched; eval reports always come from lab9.eval.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    logs = Path("reports/logs")
    logs.mkdir(parents=True, exist_ok=True)
    results = []

    def run(name, module, *args, expected=0):
        command = [sys.executable, "-m", module, *args]
        print(f"RUN {name}: python -m {module} {' '.join(args)}", flush=True)
        p = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONUTF8": "1"})
        output = p.stdout + p.stderr
        (logs / f"{name}.txt").write_text(output, encoding="utf-8")
        results.append({"name": name, "command": ["python", "-m", module, *args],
                        "expected_exit": expected, "actual_exit": p.returncode,
                        "passed": p.returncode == expected, "output": output})
        Path("reports/verification.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(output, end="", flush=True)
        if p.returncode != expected:
            raise RuntimeError(f"{name}: expected exit {expected}, got {p.returncode}")

    run("smoke", "lab9.smoke")
    run("evalset_v1", "lab9.evalset", "--build", "--check")
    run("evalset_v2", "lab9.evalset", "--v2", "--build")
    run("tests_core", "pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "lab9 and not advanced")
    run("tests_advanced", "pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "advanced")
    run("judge_tone", "lab9.judge", "--csv", "data/eval/judge_tone_public.csv", "--audit", "10")
    run("judge_helpful", "lab9.judge", "--csv", "data/eval/judge_helpful_public.csv", "--audit", "5", expected=1)
    run("baseline_v1", "lab9.eval", "--shape", "swarm", "--out", "reports/baseline_v1.json")
    run("eval_fixed", "lab9.eval", "--shape", "fixed")
    run("eval_seeded_regression", "lab9.eval", "--shape", "seeded_regression")
    run("gate_baseline", "lab9.gate", "--pr", "reports/baseline_v1.json", "--baseline", "reports/baseline_v1.json")
    run("gate_fixed", "lab9.gate", "--pr", "reports/eval_fixed.json", "--baseline", "reports/baseline_v1.json")
    run("gate_seeded", "lab9.gate", "--pr", "reports/eval_seeded_regression.json", "--baseline", "reports/baseline_v1.json", expected=1)
    run("ci_check", "lab9.ci_check", "--pr", "reports/baseline_v1.json", "--baseline", "reports/baseline_v1.json")
    run("baseline_v2", "lab9.eval", "--shape", "swarm", "--spec", "config/metric_spec_v2.yaml", "--out", "reports/baseline_v2.json")
    run("gate_baseline_v2", "lab9.gate", "--pr", "reports/baseline_v2.json", "--baseline", "reports/baseline_v2.json", "--spec", "config/metric_spec_v2.yaml")
    run("mutation", "lab9.mutation", "--spec", "config/metric_spec_v2.yaml", "--baseline", "reports/baseline_v2.json")
    run("aa", "lab9.mutation", "--spec", "config/metric_spec_v2.yaml", "--aa", "66,77,88,99,110")
    run("detection", "lab9.mutation", "--detect")
    run("slice_eval", "lab9.eval", "--shape", "slice_regression", "--spec", "config/metric_spec_v2.yaml", "--out", "reports/eval_slice_regression.json")
    run("gate_slice", "lab9.gate", "--pr", "reports/eval_slice_regression.json", "--baseline", "reports/baseline_v2.json", "--spec", "config/metric_spec_v2.yaml", expected=1)
    run("traps", "lab9.traps", "--pr", "reports/eval_slice_regression.json", "--baseline", "reports/baseline_v2.json", "--spec", "config/metric_spec_v2.yaml")
    for trap in ("evaluator_errors_as_nan", "dropped_failing_rows", "cherry_picked_seeds", "loosened_spec"):
        args = ["--pr", f"reports/traps/{trap}.json", "--baseline", "reports/baseline_v2.json", "--spec"]
        args += ["reports/traps/loosened_spec.spec.yaml", "--base-spec", "config/metric_spec_v2.yaml"] if trap == "loosened_spec" else ["config/metric_spec_v2.yaml"]
        run(f"trap_{trap}", "lab9.gate", *args, expected=1)
    run("trace_bad", "lab9.trace_case", "--shape", "seeded_regression", "--claim", "C-002", "--seed", "11")
    run("trace_fixed", "lab9.trace_case", "--shape", "fixed", "--claim", "C-002", "--seed", "11")
    run("writeup", "lab9.writeup")
    print(f"PASS: {len(results)} commands met their expected exit codes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
