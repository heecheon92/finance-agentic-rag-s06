# -*- coding: utf-8 -*-
"""검색·답변 지표.

작은 셋(40문항)에서는 전체 평균이 서사를 만들지 못한다. 유형별로 쪼개야
"조항번호형이 Hybrid 로 얼마나 올랐는가" 같은 말을 할 수 있다.
"""

from __future__ import annotations


def recall_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    """gold 청크가 상위 k 안에 하나라도 있으면 1. 근거는 여러 개일 수 있다."""
    return 1.0 if set(retrieved[:k]) & set(gold) else 0.0


def mrr(retrieved: list[str], gold: list[str]) -> float:
    for rank, cid in enumerate(retrieved, start=1):
        if cid in set(gold):
            return 1.0 / rank
    return 0.0


def precision_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    if not k:
        return 0.0
    return len(set(retrieved[:k]) & set(gold)) / k


def aggregate(rows: list[dict], ks: tuple[int, ...] = (1, 3, 5, 10)) -> dict:
    """행 하나 = 문항 하나. 전체 평균과 type 별 분해표를 같이 만든다.

    반환 형태 (results/*.json 의 overall · by_type 과 같다)
        {"overall": 블록, "by_type": {유형: 블록, ...}}
    블록 하나에 들어가는 것
        recall@k (ks 마다) · mrr · n                      — 전체 평균. 소수 4자리
        answer_rate                                       — answered 키가 있는 행이 하나라도 있을 때만.
                                                            거절하지 않고 답한 비율
        false_refusal_rate                                — answerable 인 행이 있을 때만. 답할 근거가
                                                            있는데(answerable=True) 거절한 비율
        abstain_accuracy                                  — answerable=False 인 행이 있을 때만. 거절했거나
                                                            grade 가 "insufficient"(한계를 밝힌 답)인 비율
        latency_ms_avg · latency_ms_p95                   — latency_ms 가 있는 행이 있을 때만.
                                                            p95 는 정렬한 뒤 int(n × 0.95) − 1 번째(0 미만이면 0)

    [6회차 실습 1] 이 함수를 채우세요. 테스트는 tests/test_metrics.py 입니다.
    왜 유형별인가: 40문항짜리 셋에서 전체 평균 하나로는 아무 이야기도 못 만든다. "조항번호형이
    Hybrid 로 얼마나 올랐는가"를 말하려면 유형별로 쪼개야 한다.
    왜 분모를 가르나: 오거절률(답할 수 있는데 거절)과 미답변 정확도(거절해야 할 것을 거절)는
    분모가 다르다. 둘을 한 숫자로 합치면 "전부 거절"이 좋은 점수를 받는다.
    answered=None도 미측정으로 제외한다. 빈 입력의 검색 평균은 0, n은 0이다.
    지연은 0ms도 측정값으로 포함하며 소수 1자리로 기록한다.
    """
    # raise NotImplementedError("6회차 실습 1: metrics.aggregate 를 채우세요")
    def block(subset: list[dict]) -> dict:
        n = len(subset)
        denominator = n or 1
        out = {
            f"recall@{k}": round(sum(r[f"recall@{k}"] for r in subset) / denominator, 4)
            for k in ks
        }
        out["mrr"] = round(sum(r["mrr"] for r in subset) / denominator, 4)
        out["n"] = n

        answered = [r for r in subset if r.get("answered") is not None]
        if answered:
            out["answer_rate"] = round(
                sum(bool(r["answered"]) for r in answered) / len(answered), 4
            )
            can = [r for r in answered if r.get("answerable", True)]
            if can:
                out["false_refusal_rate"] = round(
                    sum(not r["answered"] for r in can) / len(can), 4
                )
            cannot = [r for r in answered if not r.get("answerable", True)]
            if cannot:
                out["abstain_accuracy"] = round(
                    sum(not r["answered"] or r.get("grade") == "insufficient"
                        for r in cannot) / len(cannot), 4
                )

        latencies = sorted(
            r["latency_ms"] for r in subset if r.get("latency_ms") is not None
        )
        if latencies:
            out["latency_ms_avg"] = round(sum(latencies) / len(latencies), 1)
            index = max(int(len(latencies) * 0.95) - 1, 0)
            out["latency_ms_p95"] = round(latencies[index], 1)
        return out

    by_type: dict[str, list[dict]] = {}
    for row in rows:
        type_ = row.get("type", "?")
        if type_ not in by_type:
            by_type[type_] = []
        by_type[type_].append(row)
    return {
        "overall": block(rows),
        "by_type": {type_: block(subset) for type_, subset in sorted(by_type.items())},
    }


def compare(tables: dict[str, dict], metric: str = "recall@5") -> list[dict]:
    """3단계 비교표. 파이프라인별 유형 분해를 한 표로 세운다."""
    types = sorted({t for tb in tables.values() for t in tb["by_type"]})
    rows = []
    for t in types:
        row = {"type": t}
        for name, tb in tables.items():
            row[name] = tb["by_type"].get(t, {}).get(metric)
        rows.append(row)
    row = {"type": "전체"}
    for name, tb in tables.items():
        row[name] = tb["overall"].get(metric)
    rows.append(row)
    return rows
