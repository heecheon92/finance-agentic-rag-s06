"""ROI crossover must exclude shared fixed costs and baseline traffic."""
from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.mark.parametrize("daily,server_month", [(500, 300000), (2000, 900000), (0, 300000)])
def test_crossover_ignores_shared_server_cost_and_current_traffic(tmp_path, monkeypatch, daily, server_month):
    from finrag import settings

    results = tmp_path / "results"
    results.mkdir()
    # One million uncached nano input tokens cost $0.20, or 280 won.
    (results / "agentic.json").write_text(json.dumps({
        "rows": [{"usage": {"gpt-5.4-nano": {"input_tokens": 1000000, "output_tokens": 0}}}],
        "overall": {"latency_ms_avg": 1000},
    }), encoding="utf-8")
    monkeypatch.setattr(settings, "get_settings", lambda: SimpleNamespace(results_dir=results))
    monkeypatch.setattr(sys, "argv", ["roi.py", "--daily", str(daily), "--server-month", str(server_month)])
    main = runpy.run_path(str(ROOT / "scripts" / "roi.py"))["main"]
    monkeypatch.setitem(main.__globals__, "ROOT", tmp_path)
    assert main() == 0
    report = json.loads((results / "roi.json").read_text(encoding="utf-8"))
    # 43,000,000 / (36 months * 22 days * 280 won) = 193.903...
    assert report["three_year"]["breakeven_daily_questions"] == 194
