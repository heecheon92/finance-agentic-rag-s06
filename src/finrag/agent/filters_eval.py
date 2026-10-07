# -*- coding: utf-8 -*-
"""Self-Query 필터 정확도 (6회차).

골든셋의 `expected_filters`(사람이 적은 "이 질문이면 이 필터")와 에이전트가 실제로 뽑은
`filters`(5회차 결과 행)를 필드별로 맞춰 본다. 필터는 틀리면 조용히 0건이 되는 부품이라,
Recall 이 떨어졌을 때 "검색이 못 찾은 것"과 "필터가 잘라 낸 것"을 가르려면 이 숫자가 있어야 한다.

세는 것
  - 필드별 정밀도(뽑은 것 중 맞은 비율)와 재현율(있어야 할 것 중 뽑은 비율)
  - 문항 단위 완전 일치(기대한 필드가 전부 같고, 기대 밖 필드를 넣지 않음)
  - 기대 필터가 없는 문항에서 필터를 넣은 수(넣지 말았어야 할 것)
"""
from __future__ import annotations

FIELDS = ("doc_type", "issuer", "product", "generation", "effective_on")


def _clean(f: dict | None) -> dict:
    return {k: v for k, v in (f or {}).items() if k in FIELDS and v not in (None, "", [])}


def filter_accuracy(rows: list[dict], golden: list[dict]) -> dict:
    """기대 필터가 적힌 문항에서, 기대한 필드만 본다.

    기대에 없는 필드를 에이전트가 더 뽑은 것(예: 기대는 doc_type 뿐인데 issuer 도 뽑음)은 세지 않는다.
    골든셋의 expected_filters 는 "이 질문이면 최소한 이 필터"이지 "이것만"이 아니기 때문이다.
    기대 필터가 없는 문항은 평가하지 않는다(무엇이 맞는지 적혀 있지 않다).
    """
    by_id = {r["id"]: r for r in rows}
    per_field = {k: {"tp": 0, "wrong": 0, "fn": 0} for k in FIELDS}
    exact, n_expected, n_no_expected, n_missing_row = 0, 0, 0, 0
    mismatches = []
    for item in golden:
        row = by_id.get(item["id"])
        if row is None or "filters" not in row:
            n_missing_row += 1
            continue
        got = _clean(row.get("filters"))
        exp = _clean(item.get("expected_filters"))
        if not exp:
            n_no_expected += 1
            continue
        n_expected += 1
        ok = True
        for k, e in exp.items():
            g = got.get(k)
            if g == e:
                per_field[k]["tp"] += 1
            elif g is None:
                per_field[k]["fn"] += 1; ok = False
                mismatches.append({"id": item["id"], "field": k, "expected": e, "got": None})
            else:
                per_field[k]["wrong"] += 1; ok = False
                mismatches.append({"id": item["id"], "field": k, "expected": e, "got": g})
        exact += ok

    def prf(c: dict) -> dict:
        n = c["tp"] + c["wrong"] + c["fn"]
        p = c["tp"] / (c["tp"] + c["wrong"]) if c["tp"] + c["wrong"] else None
        r = c["tp"] / n if n else None
        return {**c, "n": n, "precision": round(p, 3) if p is not None else None,
                "recall": round(r, 3) if r is not None else None}

    return {"n_expected": n_expected, "exact_match": exact,
            "exact_rate": round(exact / n_expected, 4) if n_expected else None,
            "n_no_expected": n_no_expected, "n_missing_row": n_missing_row,
            "by_field": {k: prf(c) for k, c in per_field.items()},
            "mismatches": mismatches}
