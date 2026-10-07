#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM-as-Judge 를 돌린다 (6회차).

    python scripts/judge_run.py               # 자기 results/agentic.json 의 20문항 채점 → results/judge.json
    python scripts/judge_run.py --calibrate   # 강사 답변 20개를 채점해 강사 라벨과 일치도 → results/judge_calibration.json
    python scripts/judge_run.py --result results/hybrid.json   # 다른 결과 파일(답변이 있어야 한다)

루브릭은 src/finrag/eval/judge.py 의 RUBRIC. 근거 일치 · 수치·단위 · 근거 밖 주장 없음, 각 0·1·2.
거절한 문항은 0점이 아니라 채점에서 뺀다(그건 오거절률이 본다). 키가 없으면 근거 일치만 기계 채점이다.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true", help="강사 답변 20개로 judge 를 검증한다")
    ap.add_argument("--result", default="results/agentic.json")
    ap.add_argument("--ids", default="", help="쉼표로 문항 ID. 기본은 JUDGE_SET 20문항")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    from finrag.eval import harness, judge
    from finrag.llm import get_llm, is_fake
    from finrag.settings import get_settings
    s = get_settings()
    fake = is_fake(get_llm("judge", size="main"))
    if fake:
        print("[주의] LLM 키가 없어 가짜 모델입니다. 근거 일치만 기계로 매기고 나머지 둘은 0 입니다.\n")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if args.calibrate:
        path = s.golden_dir / "judge_calibration.jsonl"
        if not path.exists():
            print(f"{path.relative_to(ROOT)} 가 없습니다."); return 1
        calib = judge.load_calibration(path)
        print(f"강사 답변 {len(calib)}개를 judge 로 채점해 강사 라벨과 맞춰 봅니다.\n")
        res = judge.calibrate(calib, verbose=not args.quiet)
        a = res["agreement"]
        if a is None:
            print("\n일치도는 아직 못 냅니다. judge.agreement 가 비어 있습니다(6회차 실습 2). 채운 뒤 make judge-calibrate 를 다시 돌리면 1분 만에 나옵니다.")
        else:
          print(f"\n일치도 (n={res['n']})   완전 일치 {a['total']['exact']:.0%}   ±1 이내 {a['total']['within_1']:.0%}"
                f"   평균 절대 오차 {a['total']['mae']:.2f}점(6점 만점)   judge − 사람 평균 {res['judge_minus_human_avg']:+.2f}")
          print(f"{'항목':16}{'완전 일치':>10}{'±1 이내':>10}{'MAE':>8}")
          for k in judge.ITEMS:
            print(f"{k:16}{a[k]['exact']:>10.0%}{a[k]['within_1']:>10.0%}{a[k]['mae']:>8.2f}")
        res.update({"generated_at": now, "llm": "fake" if fake else s.llm_model_main})
        out = s.results_dir / "judge_calibration.json"
    else:
        rp = ROOT / args.result
        if not rp.exists():
            print(f"{args.result} 가 없습니다. make agentic 을 먼저 돌리세요."); return 1
        result = json.loads(rp.read_text(encoding="utf-8"))
        golden, gold_ids = harness.load_golden()
        ids = [x.strip() for x in args.ids.split(",") if x.strip()] or None
        print(f"{args.result} 의 {len(ids or judge.JUDGE_SET)}문항을 채점합니다 (근거 일치 · 수치·단위 · 근거 밖 주장 없음, 각 0~2).\n")
        res = judge.score_result(result, golden, gold_ids, ids=ids, verbose=not args.quiet)
        m = res["mean_by_item"]
        print(f"\n[judge] {res['n']}문항 중 채점 {res['n_scored']} (거절 {res['n_refused']})   평균 {res['mean_total']:.2f}/6"
              f"   만점 {res['full_marks']}개   근거 일치 {m['basis_match']:.2f} · 수치 {m['numeric_ok']:.2f} · 근거 밖 주장 없음 {m['no_extra_claim']:.2f}")
        for t, b in res["by_type"].items():
            print(f"  {t:12}{b['n']:>3}문항  평균 {b['mean_total']:.2f}  ({b['basis_match']:.2f} · {b['numeric_ok']:.2f} · {b['no_extra_claim']:.2f})")
        res.update({"generated_at": now, "llm": "fake" if fake else s.llm_model_main, "source": args.result})
        out = s.results_dir / "judge.json"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("→", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
