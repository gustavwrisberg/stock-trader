"""Run the stock-analysis skill's own scorer (score.py) on each company.

The skill is vendored, unmodified, at .claude/skills/stock-analysis. We call its
script as a black box so the scoring logic, sector benchmarks and red-flag gates
stay exactly what the skill defines -- update the skill folder to update the method.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / ".claude" / "skills" / "stock-analysis"
SCORE_PY = SKILL_DIR / "scripts" / "score.py"


def score_company(ticker: str, name: str, sector: str, as_of: str, computed: Dict[str, Any],
                  manual_flags: Dict[str, Any], preset: str = "default") -> Dict[str, Any]:
    flags = dict(computed.get("flags") or {})
    flags.update(manual_flags or {})
    payload = {
        "company": name,
        "ticker": ticker,
        "as_of": as_of,
        "basis": "consolidated",
        "currency": "USD-listed",
        "sector": sector,
        "metrics": computed.get("metrics") or {},
        "flags": flags,
    }
    proc = subprocess.run(
        [sys.executable, "-I", str(SCORE_PY), "--json", "--preset", preset, "-"],
        input=json.dumps(payload), capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout).strip()[-400:]}
    r = json.loads(proc.stdout)
    gates = r.get("gates") or {}
    return {
        "sector_key": r.get("sector_key"),
        "sector_label": r.get("sector_label"),
        "period": computed.get("period"),
        "composite": gates.get("composite_final", r.get("composite")),
        "composite_raw": r.get("composite_raw"),
        "grade": r.get("grade"),
        "confident": r.get("composite_confident"),
        "category_coverage": r.get("category_coverage"),
        "coverage_reasons": r.get("coverage_reasons") or [],
        "categories": {k: v.get("score") for k, v in (r.get("categories") or {}).items()},
        "vetoed": bool(gates.get("vetoed")),
        "gates": [{"id": g["id"], "label": g["label"], "severity": g["severity"], "cap": g.get("cap"),
                   "evidence": g.get("evidence")} for g in gates.get("raised") or []],
        "metrics": [
            {"key": d["key"], "label": d["label"], "category": d["category"], "value": d.get("value"),
             "sub_score": d.get("sub_score"), "band": d.get("band"), "note": d.get("note")}
            for d in r.get("details") or [] if d.get("scored")
        ],
    }
