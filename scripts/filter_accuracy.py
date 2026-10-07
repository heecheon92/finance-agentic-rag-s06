#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-Query 필터 정확도 (6회차).

    python scripts/filter_accuracy.py                       # results/agentic.json → results/filter_accuracy.json
    python scripts/filter_accuracy.py --result results/agentic_sample.json

골든셋의 expected_filters 와 에이전트가 뽑은 filters 를 필드별로 맞춰 본다. LLM 호출 없음, 1초.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", default="results/agentic.json")
    args = ap.parse_args()

    from finrag.eval import harness
    from finrag.eval.filters_eval import FIELDS, filter_accuracy
    from finrag.settings import get_settings
    s = get_settings()
    rp = ROOT / args.result
    if not rp.exists():
        print(f"{args.result} 가 없습니다."); return 1
    result = json.loads(rp.read_text(encoding="utf-8"))
    if not any("filters" in r for r in result.get("rows", [])):
        print("결과 행에 filters 가 없습니다. 5회차 코드(10/8 이후)로 make agentic 을 다시 돌리세요."); return 1
    golden, _ = harness.load_golden()
    res = filter_accuracy(result["rows"], golden)

    print(f"기대 필터가 적힌 문항 {res['n_expected']}개 중 기대한 필드가 전부 맞은 것 {res['exact_match']} ({res['exact_rate']:.0%})")
    print(f"기대 필터가 없는 문항 {res['n_no_expected']}개는 평가하지 않음. 기대에 없는 필드를 더 뽑은 것도 세지 않음\n")
    print(f"{'필드':14}{'기대':>6}{'맞음':>6}{'다른 값':>8}{'놓침':>6}{'정밀도':>8}{'재현율':>8}")
    for k in FIELDS:
        c = res["by_field"][k]
        if not c["n"]:
            continue
        p = f"{c['precision']:.0%}" if c["precision"] is not None else "-"
        r = f"{c['recall']:.0%}" if c["recall"] is not None else "-"
        print(f"{k:14}{c['n']:>6}{c['tp']:>6}{c['wrong']:>8}{c['fn']:>6}{p:>8}{r:>8}")
    if res["mismatches"]:
        print("\n어긋난 것")
        for m in res["mismatches"][:25]:
            print(f"  {m['id']} {m['field']:14} 기대 {m['expected']!s:16} 뽑음 {m['got']!s}")
    res["source"] = args.result
    out = s.results_dir / "filter_accuracy.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n→", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
