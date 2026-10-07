#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""계산 정확도, 끝에서 끝까지 (6회차).

    python scripts/calc_e2e.py                 # 계산 골든셋 15문항 → results/calc_e2e.json (약 4~5분)
    python scripts/calc_e2e.py --only C06      # 하나만

5회차 골든 테스트(tests/test_calc_golden.py)는 함수에 값을 직접 넣어 산식이 맞는지 본다.
여기서는 질문을 에이전트에 넣어 검색 → 파라미터 추출 → 계산까지 다 지나온 값을 본다.
둘의 차이가 "함수는 맞는데 추출이 틀린" 문항이다.

맞은 것으로 치는 것
  - 기대값과 같다(금액은 1원도 다르면 틀림, 이율은 아주 작은 오차만)
  - 또는 alternatives 의 값과 같다(절사 규칙이 다른 정답). 어느 규칙인지 같이 적는다
  - 범위형(C10) · 미답변형(C15)은 계산하지 않은 것이 정답이다
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "pipelines"))


def close_enough(got, expected) -> bool:
    if isinstance(expected, int) and float(got).is_integer():
        return int(got) == expected
    return abs(float(got) - float(expected)) < 5e-7


def match(item: dict, got) -> tuple[bool, str]:
    exp = item["expected"]
    unit = exp.get("unit")
    if unit in ("range", "abstain") or not isinstance(exp.get("value"), (int, float)):
        return (got is None, "계산 안 함이 정답" if got is None else "숫자를 만듦")
    if got is None:
        return (False, "계산 안 함")
    if close_enough(got, exp["value"]):
        return (True, "기대값")
    for a in item.get("alternatives", []):
        v = a.get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool) and close_enough(got, v):
            return (True, f"대안: {a.get('label') or a.get('rounding_rule')}")
    return (False, "값이 다름")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    from finrag.llm import get_llm, is_fake
    from finrag.settings import get_settings
    import agentic
    s = get_settings()
    fake = is_fake(get_llm("extract", size="main"))
    if fake:
        print("[주의] LLM 키가 없어 가짜 모델입니다. 파라미터 추출이 안 되므로 전부 '계산 안 함' 입니다.\n")

    golden = [json.loads(l) for l in (s.golden_dir / "calc_golden.jsonl").open(encoding="utf-8") if l.strip()]
    if args.only:
        golden = [g for g in golden if g["id"] in set(args.only)]
    if args.limit:
        golden = golden[:args.limit]

    run = agentic.build()
    rows = []
    for item in golden:
        t0 = time.perf_counter()
        try:
            out = run(item["question"])
            err = None
        except Exception as e:  # noqa: BLE001 — 한 문항이 죽어도 끝까지 간다
            out, err = {}, f"{type(e).__name__}: {e}"
        ms = round((time.perf_counter() - t0) * 1000)
        c = out.get("calc") or {}
        got = c.get("value")
        ok, how = match(item, got)
        row = {"id": item["id"], "family": item.get("family"), "form": item.get("form"),
               "expected": item["expected"], "got": got, "unit": c.get("unit"),
               "tool": c.get("tool"), "abstain_reason": c.get("abstain_reason"),
               "matched": ok, "how": how, "grade": out.get("grade"),
               "retry_count": out.get("retry_count", 0), "answered": not out.get("abstained", True),
               "latency_ms": ms, "answer": (out.get("answer") or "")[:300]}
        if err:
            row["error"] = err
        rows.append(row)
        e = item["expected"]
        exp_s = f"{e['value']:,}{e.get('unit', '')}" if isinstance(e.get("value"), (int, float)) else f"({e.get('unit')})"
        got_s = f"{got:,}{c.get('unit', '')}" if isinstance(got, (int, float)) else "계산 안 함"
        print(f"  {'O' if ok else 'X'} {item['id']} {str(item.get('family', ''))[:22]:24} 기대 {exp_s:>14}  결과 {got_s:>14}  {how}  {ms / 1000:.0f}초")

    n = len(rows)
    matched = sum(1 for r in rows if r["matched"])
    res = {"n": n, "matched": matched, "accuracy": round(matched / n, 4) if n else None,
           "by_how": {}, "rows": rows,
           "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "llm": "fake" if fake else s.llm_model_main}
    for r in rows:
        res["by_how"][r["how"]] = res["by_how"].get(r["how"], 0) + 1
    print(f"\n[calc_e2e] {n}문항  맞음 {matched} ({res['accuracy']:.0%})  " +
          "  ".join(f"{k} {v}" for k, v in res["by_how"].items()))
    out = s.results_dir / "calc_e2e.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("→", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
