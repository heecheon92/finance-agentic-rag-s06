# -*- coding: utf-8 -*-
"""6회차 실습 1 자기 확인 — metrics.aggregate.

    make test        (Windows: .venv\\Scripts\\python -m pytest -q)

행 다섯 개짜리 작은 결과로 전체 평균과 유형별 분해를 손으로 계산한 값과 맞춰 본다.
키도 Qdrant 도 필요 없다. 채우기 전에는 NotImplementedError 로 실패한다. 그게 정상이다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finrag.eval.metrics import aggregate  # noqa: E402


def _row(type_: str, r1, r5, r10, mrr, *, answered=None, answerable=True, grade=None, latency=None):
    row = {"id": f"{type_}{latency}", "type": type_, "recall@1": r1, "recall@3": r5, "recall@5": r5,
           "recall@10": r10, "mrr": mrr, "answerable": answerable}
    if answered is not None:
        row["answered"] = answered
    if grade:
        row["grade"] = grade
    if latency:
        row["latency_ms"] = latency
    return row


ROWS = [
    _row("X", 1, 1, 1, 1.0, answered=True, latency=100),                                   # 답함
    _row("X", 0, 1, 1, 0.5, answered=False, latency=200),                                  # 답할 수 있는데 거절 → 오거절
    _row("Y", 0, 0, 1, 0.1, answered=True, answerable=False, grade="insufficient", latency=300),  # 한계를 밝힌 답 → 미답변 정답
    _row("Y", 0, 0, 0, 0.0, answered=True, answerable=False, grade="sufficient", latency=400),    # 숫자를 만듦 → 미답변 오답
    _row("Y", 1, 1, 1, 1.0, answered=False, answerable=False, latency=500),                # 거절 → 미답변 정답
]


def test_overall_recall_and_mrr_are_plain_averages():
    o = aggregate(ROWS)["overall"]
    assert o["n"] == 5
    assert o["recall@1"] == pytest.approx(0.4)
    assert o["recall@5"] == pytest.approx(0.6)
    assert o["recall@10"] == pytest.approx(0.8)
    assert o["mrr"] == pytest.approx(0.52)


def test_by_type_splits_rows_by_type_field():
    bt = aggregate(ROWS)["by_type"]
    assert set(bt) == {"X", "Y"}
    assert bt["X"]["n"] == 2 and bt["Y"]["n"] == 3
    assert bt["X"]["mrr"] == pytest.approx(0.75)
    assert bt["X"]["recall@1"] == pytest.approx(0.5)


def test_answer_rate_counts_answered_rows():
    o = aggregate(ROWS)["overall"]
    assert o["answer_rate"] == pytest.approx(0.6)        # 5개 중 3개가 답함


def test_false_refusal_denominator_is_answerable_rows_only():
    """오거절률 = 답할 근거가 있는 문항(answerable) 중 거절한 비율. 미답변형은 분모에 넣지 않는다."""
    agg = aggregate(ROWS)
    assert agg["overall"]["false_refusal_rate"] == pytest.approx(0.5)   # X 둘 중 하나 거절
    assert "false_refusal_rate" not in agg["by_type"]["Y"]              # Y 는 전부 미답변형이라 분모가 없다


def test_abstain_accuracy_counts_refusal_and_insufficient_answers():
    """미답변 정확도 = 거절해야 할 문항 중 거절했거나 '근거 부족' 판정으로 한계를 밝힌 답을 한 비율."""
    agg = aggregate(ROWS)
    assert agg["overall"]["abstain_accuracy"] == pytest.approx(2 / 3, abs=1e-3)   # 파일에는 소수 4자리로 적힌다
    assert "abstain_accuracy" not in agg["by_type"]["X"]


def test_latency_avg_and_p95():
    o = aggregate(ROWS)["overall"]
    assert o["latency_ms_avg"] == pytest.approx(300.0)
    assert o["latency_ms_p95"] == pytest.approx(400.0)    # 5개의 95% 자리 = 정렬한 뒤 네 번째


def test_rows_without_answered_field_have_no_answer_metrics():
    """baseline · hybrid 결과에는 answered 가 없다. 그러면 답변률 자리가 없어야 한다(0 이 아니다)."""
    rows = [_row("X", 1, 1, 1, 1.0, latency=10), _row("X", 0, 0, 0, 0.0, latency=20)]
    o = aggregate(rows)["overall"]
    assert "answer_rate" not in o and "false_refusal_rate" not in o and "abstain_accuracy" not in o
    assert o["recall@5"] == pytest.approx(0.5)


def test_reaggregating_a_saved_result_reproduces_its_summary():
    """results/agentic.json 의 rows 를 다시 집계하면 파일에 적힌 overall 과 같아야 한다. 같은 자인지 확인."""
    p = ROOT / "results" / "agentic.json"
    if not p.exists():
        pytest.skip("results/agentic.json 없음")
    r = json.loads(p.read_text(encoding="utf-8"))
    o = aggregate(r["rows"])["overall"]
    for k in ("recall@5", "mrr", "answer_rate", "false_refusal_rate", "abstain_accuracy"):
        if k in r["overall"]:
            assert o[k] == pytest.approx(r["overall"][k], abs=1e-4), k
