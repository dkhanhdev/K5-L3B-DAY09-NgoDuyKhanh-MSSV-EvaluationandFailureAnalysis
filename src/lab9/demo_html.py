"""Build one offline HTML demo from committed Lab 9 reports. Run from src/."""
from pathlib import Path
import json

from lab9.eval import load_spec
from lab9.gate import check


def main():
    root = Path(__file__).resolve().parents[2]
    reports = root / "src/reports"
    read = lambda name: json.loads((reports / f"{name}.json").read_text(encoding="utf-8"))
    evidence = read("submission_evidence")
    specs = {"v1": load_spec(root / "src/config/metric_spec.yaml"),
             "v2": load_spec(root / "src/config/metric_spec_v2.yaml")}
    cases = []
    for name, title, ver in (("baseline_v1", "Swarm · baseline", "v1"),
                              ("eval_fixed", "Fixed · đã sửa lỗi", "v1"),
                              ("eval_seeded_regression", "Seeded regression", "v1"),
                              ("eval_slice_regression", "Slice regression", "v2")):
        rep = read(name)
        base = read("baseline_" + ver)
        blocked, lines = check(rep, base, specs[ver], specs[ver])
        cases.append({"name": name, "title": title, "version": ver,
                      "run_id": rep["run_id"], "manifest": rep["manifest"],
                      "metrics": rep["metrics"], "blocked": blocked, "lines": lines})
    traces = []
    for fm, e in evidence["taxonomy_evidence"].items():
        traces.append({"fm": fm, "claim": e["claim_id"], "bug": e["bug"], "step": e["step"],
                       "events": e["trial"]["events"], "control_events": e["control"]["events"],
                       "snapshot": e["trial"]["snapshot"], "control_snapshot": e["control"]["snapshot"],
                       "label": e["label"], "scores": e["scores"]})
    data = {"cases": cases, "specs": specs, "traces": traces,
            "tone": evidence["judge_tone"], "helpful": evidence["judge_helpful"],
            "bonus": read("bonus_inspect"), "ci": evidence["pass_rate_delta_ci"],
            "logs": {name: (reports / f"logs/{name}.txt").read_text(encoding="utf-8")
                     for name in ("mutation", "aa", "detection", "traps")}}
    template = Path(__file__).with_name("demo_template.html").read_text(encoding="utf-8")
    encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    assert template.count("/*__LAB_DATA__*/") == 1
    out = root / "demo/index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(template.replace("/*__LAB_DATA__*/", encoded), encoding="utf-8", newline="\n")
    print(f"wrote {out} ({out.stat().st_size:,} bytes); 4 gate cases, 9 traces, 198 bonus comparisons")


if __name__ == "__main__":
    main()
