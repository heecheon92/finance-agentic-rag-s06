# -*- coding: utf-8 -*-
"""3단계 비교표. results/*.json 을 읽어 표로 세운다 (6회차).

파일에 적힌 요약(overall · by_type)을 그대로 믿지 않고 `rows` 에서 다시 집계한다.
세 파일이 서로 다른 날, 다른 코드로 만들어졌어도 같은 자(metrics.aggregate)로 다시 재야
한 표에 놓을 수 있다. 6회차 실습 1 이 그 자를 채운다.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from ..settings import get_settings
from . import cost
from .metrics import aggregate, compare

STAGES = ("baseline", "hybrid", "agentic")
METRICS = ["recall@1", "recall@5", "recall@10", "mrr", "answer_rate", "false_refusal_rate",
           "abstain_accuracy", "latency_ms_avg", "latency_ms_p95"]


def load(stages: tuple[str, ...] = STAGES, *, reaggregate: bool = True) -> dict[str, dict]:
    s = get_settings()
    out = {}
    for name in stages:
        p = s.results_dir / f"{name}.json"
        if not p.exists():
            continue
        r = json.loads(p.read_text(encoding="utf-8"))
        if reaggregate and r.get("rows"):
            agg = aggregate(r["rows"])
            r["overall"], r["by_type"] = agg["overall"], agg["by_type"]
        out[name] = r
    return out


def build_table(results: dict[str, dict], metric: str = "recall@5") -> list[dict]:
    return compare(results, metric)


def summary(results: dict[str, dict]) -> list[dict]:
    """전체 행 하나씩: 단계 × (지표 아홉 + 문항당 비용)."""
    rows = []
    for name, r in results.items():
        o = r["overall"]
        c = cost.summarize(r)
        rows.append({"stage": name, **{m: o.get(m) for m in METRICS},
                     "tokens_in_avg": c["tokens_in_avg"], "tokens_out_avg": c["tokens_out_avg"],
                     "cost_krw_avg": c["cost_krw_avg"], "n": o.get("n")})
    return rows


def write_csv(results: dict[str, dict], path: Path | None = None) -> Path:
    s = get_settings()
    path = path or s.results_dir / "compare.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    types = sorted({t for r in results.values() for t in r["by_type"]}) + ["전체"]
    rows = []
    for t in types:
        for m in METRICS:
            row = {"type": t, "metric": m}
            for name, r in results.items():
                blk = r["overall"] if t == "전체" else r["by_type"].get(t, {})
                row[name] = blk.get(m)
            if any(row.get(n) is not None for n in results):
                rows.append(row)
    for name, r in results.items():
        c = cost.summarize(r)
        for m in ("tokens_in_avg", "tokens_out_avg", "cost_krw_avg"):
            row = next((x for x in rows if x["type"] == "전체" and x["metric"] == m), None)
            if row is None:
                row = {"type": "전체", "metric": m}; rows.append(row)
            row[name] = c[m]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["type", "metric", *results.keys()])
        w.writeheader()
        w.writerows(rows)
    return path


def _fmt(metric: str, v) -> str:
    if v is None:
        return "-"
    if metric.startswith("latency"):
        return f"{v / 1000:.1f}초"
    if metric in ("mrr",):
        return f"{v:.3f}"
    if metric.startswith("tokens"):
        return f"{v:,}"
    if metric.startswith("cost"):
        return f"{v:.1f}원"
    return f"{v:.1%}"


def print_table(results: dict[str, dict], metric: str = "recall@5") -> None:
    names = list(results)
    w = max(max((len(n) for n in names), default=8) + 2, 11)
    print(f"\n{metric} 유형별 비교")
    print(f"{'유형':<14}" + "".join(f"{n:>{w}}" for n in names) + f"{'Δ(첫→끝)':>11}")
    print("-" * (14 + w * len(names) + 11))
    for row in build_table(results, metric):
        vals = [row.get(n) for n in names]
        cells = "".join(f"{(f'{v:.1%}' if v is not None else '-'):>{w}}" for v in vals)
        d = ""
        if vals[0] is not None and vals[-1] is not None and len(names) > 1:
            d = f"{(vals[-1] - vals[0]) * 100:+.1f}%p"
        print(f"{row['type']:<14}{cells}{d:>11}")


def print_summary(results: dict[str, dict]) -> None:
    """3단계 전체 표. 슬라이드 한 장이 이 표다."""
    names = list(results)
    w = max(max((len(n) for n in names), default=8) + 2, 11)
    print(f"\n{'지표':<20}" + "".join(f"{n:>{w}}" for n in names))
    print("-" * (20 + w * len(names)))
    rows = {r["stage"]: r for r in summary(results)}
    for m in [*METRICS, "tokens_in_avg", "tokens_out_avg", "cost_krw_avg"]:
        print(f"{m:<20}" + "".join(f"{_fmt(m, rows[n].get(m)):>{w}}" for n in names))


def main() -> int:
    t = load()
    if not t:
        print("results/ 에 baseline.json · hybrid.json · agentic.json 이 없습니다.")
        return 1
    print_summary(t)
    print_table(t, "recall@5")
    print_table(t, "mrr")
    print("\n→", write_csv(t))
    return 0
