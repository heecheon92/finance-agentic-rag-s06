# -*- coding: utf-8 -*-
"""비용. 결과 파일의 토큰 사용량을 돈으로 바꾼다 (6회차 ROI).

검색(임베딩·BM25·리랭커)은 로컬에서 돌아 API 비용이 0 이다. 돈이 드는 것은 LLM 호출뿐이고,
그 호출은 에이전트 파이프라인(5회차)에만 있다. 그래서 baseline · hybrid 의 비용은 0 이고
agentic 의 비용은 `results/agentic.json` 의 문항별 `usage`(모델별 입력·출력 토큰)에서 나온다.

단가는 모델 이름의 앞부분으로 찾는다. "gpt-5.4-mini-2026-03-05" 같은 날짜 붙은 이름도 잡는다.
단가표의 날짜와 출처를 같이 적어 둔다. 바뀌면 이 표만 고친다.
"""
from __future__ import annotations

# USD / 1M 토큰. 2026-10-08 조회, https://developers.openai.com/docs/models/gpt-5.4-mini · gpt-5.4-nano
PRICES_USD_PER_M = {
    "gpt-5.4-mini": {"input": 0.75, "cached": 0.075, "output": 4.50},
    "gpt-5.4-nano": {"input": 0.20, "cached": 0.02, "output": 1.25},
}
PRICES_AS_OF = "2026-10-08"
USD_KRW = 1400.0        # 가정값. ROI 문서에 환율 가정을 적는다.


def price_for(model: str) -> dict | None:
    for name, p in PRICES_USD_PER_M.items():
        if model.startswith(name):
            return p
    return None


def cost_usd(usage: dict) -> float:
    """문항 하나의 usage({모델: {input_tokens, output_tokens, input_token_details…}}) → USD."""
    total = 0.0
    for model, u in (usage or {}).items():
        p = price_for(model)
        if not p:
            continue
        inp = u.get("input_tokens", 0)
        cached = (u.get("input_token_details") or {}).get("cache_read", 0)
        out = u.get("output_tokens", 0)
        total += ((inp - cached) * p["input"] + cached * p["cached"] + out * p["output"]) / 1e6
    return total


def tokens(usage: dict) -> tuple[int, int]:
    """(입력, 출력) 토큰 합. 모델 구분 없이."""
    i = sum(u.get("input_tokens", 0) for u in (usage or {}).values())
    o = sum(u.get("output_tokens", 0) for u in (usage or {}).values())
    return i, o


def summarize(result: dict) -> dict:
    """결과 파일 하나의 문항당 토큰·비용. usage 가 없는 파일(baseline·hybrid)은 전부 0."""
    rows = result.get("rows", [])
    with_usage = [r for r in rows if r.get("usage")]
    n = len(with_usage)
    by_model: dict[str, dict] = {}
    for r in with_usage:
        for model, u in r["usage"].items():
            b = by_model.setdefault(model, {"input_tokens": 0, "output_tokens": 0, "calls": 0})
            b["input_tokens"] += u.get("input_tokens", 0)
            b["output_tokens"] += u.get("output_tokens", 0)
            b["calls"] += 1
    costs = [cost_usd(r["usage"]) for r in with_usage]
    toks = [tokens(r["usage"]) for r in with_usage]
    retried = [r for r in rows if r.get("retry_count")]
    return {
        "n": len(rows), "n_with_usage": n,
        "tokens_in_avg": round(sum(t[0] for t in toks) / n) if n else 0,
        "tokens_out_avg": round(sum(t[1] for t in toks) / n) if n else 0,
        "cost_usd_avg": round(sum(costs) / n, 6) if n else 0.0,
        "cost_usd_max": round(max(costs), 6) if n else 0.0,
        "cost_krw_avg": round(sum(costs) / n * USD_KRW, 2) if n else 0.0,
        "retry_share": round(len(retried) / len(rows), 4) if rows else 0.0,
        "by_model": {m: {**b, "input_avg": round(b["input_tokens"] / n), "output_avg": round(b["output_tokens"] / n)}
                     for m, b in by_model.items()} if n else {},
        "prices_as_of": PRICES_AS_OF, "usd_krw": USD_KRW,
    }


def monthly(result: dict, daily_questions: int = 500, days: int = 22, usd_krw: float = USD_KRW) -> dict:
    """월 API 비용. 일 질문 수 × 영업일 × 문항당 비용. 가정값은 전부 인자로 받아 문서에 적게 한다."""
    s = summarize(result)
    per_q = s["cost_usd_avg"]
    month_q = daily_questions * days
    usd = per_q * month_q
    return {"daily_questions": daily_questions, "days": days, "monthly_questions": month_q,
            "cost_usd_per_q": per_q, "monthly_usd": round(usd, 2), "monthly_krw": round(usd * usd_krw),
            "yearly_krw": round(usd * usd_krw * 12), "usd_krw": usd_krw}
