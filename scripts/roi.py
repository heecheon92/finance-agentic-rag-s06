#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROI 계산 (6회차). 결과 파일의 토큰을 돈으로, 가정값을 월 비용과 절감으로.

    python scripts/roi.py                                  # 기본 가정값으로 → results/roi.json
    python scripts/roi.py --daily 2000 --minutes-saved 2   # 가정을 바꿔 본다

가정값은 전부 인자다. 어느 것도 측정값이 아니므로 docs/roi.md 에 "가정"이라고 적는다.
측정값은 둘뿐이다: 문항당 토큰(results/agentic.json 의 usage)과 문항당 지연(latency_ms).
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
    ap.add_argument("--daily", type=int, default=500, help="일 질문 수(가정). 상담 보조 화면 기준")
    ap.add_argument("--days", type=int, default=22, help="월 영업일(가정)")
    ap.add_argument("--usd-krw", type=float, default=1400.0, help="환율(가정)")
    ap.add_argument("--server-month", type=int, default=300_000, help="CPU 서버 1대 월 비용(가정). 임베딩·리랭커·Qdrant 가 여기서 돈다")
    ap.add_argument("--gpu-capex", type=int, default=25_000_000, help="내부망 GPU 서버 구매(가정)")
    ap.add_argument("--gpu-opex-year", type=int, default=6_000_000, help="GPU 서버 연 운영비(전기·상면·관리, 가정)")
    ap.add_argument("--minutes-saved", type=float, default=3.0, help="상담 건당 절감 분(가정)")
    ap.add_argument("--hourly-wage", type=int, default=25_000, help="상담사 시간당 인건비(가정)")
    args = ap.parse_args()

    from finrag.eval import cost
    from finrag.settings import get_settings
    s = get_settings()
    ap_ = s.results_dir / "agentic.json"
    if not ap_.exists():
        print("results/agentic.json 이 없습니다."); return 1
    ag = json.loads(ap_.read_text(encoding="utf-8"))
    hy_path = s.results_dir / "hybrid.json"
    hy = json.loads(hy_path.read_text(encoding="utf-8")) if hy_path.exists() else {}
    if not any(r.get("usage") for r in ag.get("rows", [])):
        print("결과 행에 usage 가 없습니다. 5회차 코드(10/8 이후)로 make agentic 을 다시 돌리세요."); return 1

    c = cost.summarize(ag)
    m = cost.monthly(ag, daily_questions=args.daily, days=args.days, usd_krw=args.usd_krw)
    lat = ag.get("overall", {}).get("latency_ms_avg")
    lat_h = hy.get("overall", {}).get("latency_ms_avg")

    api_month = m["monthly_krw"]
    infra_month = args.server_month
    total_month = api_month + infra_month
    api_3y = total_month * 36
    gpu_3y = args.gpu_capex + args.gpu_opex_year * 3 + infra_month * 36   # GPU 서버에도 운영 서버 비용은 든다
    saved_month = round(m["monthly_questions"] * args.minutes_saved / 60 * args.hourly_wage)
    net_month = saved_month - total_month
    payback = None  # 초기 투자가 없는 API 안은 회수 기간이 0 이다. GPU 안만 계산한다
    if net_month > 0:
        payback = round((args.gpu_capex) / (saved_month - (args.gpu_opex_year / 12 + infra_month)), 1) \
            if saved_month > args.gpu_opex_year / 12 + infra_month else None

    print("측정값 (results/agentic.json, usage 가 있는 문항 %d개)" % c["n_with_usage"])
    print(f"  문항당 토큰   입력 {c['tokens_in_avg']:,} · 출력 {c['tokens_out_avg']:,}")
    for model, b in c["by_model"].items():
        print(f"    {model:20} 입력 {b['input_avg']:>6,}  출력 {b['output_avg']:>5,}  (문항당 평균)")
    print(f"  문항당 비용   ${c['cost_usd_avg']:.5f} = {c['cost_krw_avg']:.1f}원  (최대 {c['cost_usd_max'] * args.usd_krw:.0f}원, 재검색한 문항 비율 {c['retry_share']:.0%})")
    print(f"  문항당 지연   agentic {lat / 1000:.1f}초" + (f" · hybrid {lat_h / 1000:.1f}초" if lat_h else ""))
    print(f"  단가 기준     {c['prices_as_of']} (USD/1M 토큰: " +
          ", ".join(f"{k} 입력 {v['input']} · 출력 {v['output']}" for k, v in cost.PRICES_USD_PER_M.items()) + ")")
    print(f"\n가정값  일 {args.daily:,}건 × {args.days}일 = 월 {m['monthly_questions']:,}건, 환율 {args.usd_krw:,.0f}원, "
          f"CPU 서버 월 {infra_month:,}원, 건당 {args.minutes_saved}분 절감 × 시급 {args.hourly_wage:,}원")
    print(f"\n{'항목':24}{'월':>14}{'3년':>16}")
    print(f"{'LLM API 비용':24}{api_month:>13,}원{api_month * 36:>15,}원")
    print(f"{'서버(CPU 1대)':24}{infra_month:>13,}원{infra_month * 36:>15,}원")
    print(f"{'합계 (외부 API 안)':24}{total_month:>13,}원{api_3y:>15,}원")
    print(f"{'내부망 GPU 안 (3년 TCO)':24}{'':>14}{gpu_3y:>15,}원   구매 {args.gpu_capex:,} + 운영 {args.gpu_opex_year:,}/년 + 서버")
    print(f"{'상담 시간 절감':24}{saved_month:>13,}원{saved_month * 36:>15,}원")
    print(f"{'순 효과 (API 안)':24}{net_month:>13,}원{net_month * 36:>15,}원")
    if payback is not None:
        print(f"  GPU 안 회수 기간 약 {payback}개월 (절감에서 운영비를 뺀 돈으로 구매비를 갚는 데 걸리는 달)")
    print(f"\n  API 안이 GPU 안보다 3년에 {gpu_3y - api_3y:,}원 {'싸다' if gpu_3y > api_3y else '비싸다'}. "
          f"손익이 뒤집히는 일 질문 수는 약 {round(args.daily * gpu_3y / api_3y) if api_3y else 0:,}건이다(선형 가정).")

    res = {"measured": {"tokens_in_avg": c["tokens_in_avg"], "tokens_out_avg": c["tokens_out_avg"],
                        "by_model": c["by_model"], "cost_usd_per_q": c["cost_usd_avg"],
                        "cost_krw_per_q": c["cost_krw_avg"], "retry_share": c["retry_share"],
                        "latency_ms_avg": lat, "hybrid_latency_ms_avg": lat_h, "prices_as_of": c["prices_as_of"]},
           "assumptions": vars(args),
           "monthly": {"questions": m["monthly_questions"], "api_krw": api_month, "infra_krw": infra_month,
                       "total_krw": total_month, "saved_krw": saved_month, "net_krw": net_month},
           "three_year": {"api_plan_krw": api_3y, "gpu_plan_krw": gpu_3y, "payback_months_gpu": payback,
                          "breakeven_daily_questions": round(args.daily * gpu_3y / api_3y) if api_3y else None},
           "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    out = s.results_dir / "roi.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n→", out.relative_to(ROOT), " (docs/roi.md 의 표에 옮겨 적는다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
