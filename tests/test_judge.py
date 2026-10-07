# -*- coding: utf-8 -*-
"""6회차 실습 2 자기 확인 — judge.agreement, 그리고 비용 계산.

judge 의 일치도는 LLM 없이 숫자 두 줄로 잰다. 채우기 전에는 NotImplementedError 로 실패한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finrag.eval import cost  # noqa: E402
from finrag.eval.judge import JUDGE_SET, agreement  # noqa: E402


def test_agreement_empty_is_n_zero():
    assert agreement([], []) == {"n": 0}


def test_agreement_exact_and_within_one():
    judge = [6, 5, 4, 2, 0]
    human = [6, 4, 4, 4, 1]
    a = agreement(judge, human)
    assert a["n"] == 5
    assert a["exact"] == pytest.approx(0.4)        # 6=6, 4=4
    assert a["within_1"] == pytest.approx(0.8)     # 2 vs 4 만 밖
    assert a["mae"] == pytest.approx(0.8)          # (0+1+0+2+1)/5


def test_agreement_uses_shorter_length():
    a = agreement([2, 2, 2], [2, 0])
    assert a["n"] == 2 and a["exact"] == pytest.approx(0.5)


def test_judge_set_is_twenty_answerable_questions():
    assert len(JUDGE_SET) == 20 and "S39" not in JUDGE_SET and "S40" not in JUDGE_SET


def test_cost_uses_model_prefix_and_cached_rate():
    usage = {"gpt-5.4-nano-2026-01-01": {"input_tokens": 1_000_000, "output_tokens": 0,
                                         "input_token_details": {"cache_read": 500_000}},
             "gpt-5.4-mini": {"input_tokens": 0, "output_tokens": 1_000_000}}
    usd = cost.cost_usd(usage)
    assert usd == pytest.approx(0.5 * 0.20 + 0.5 * 0.02 + 4.50)


def test_cost_summary_is_zero_without_usage():
    s = cost.summarize({"rows": [{"id": "S01"}, {"id": "S02"}]})
    assert s["n_with_usage"] == 0 and s["cost_usd_avg"] == 0.0 and s["tokens_in_avg"] == 0
