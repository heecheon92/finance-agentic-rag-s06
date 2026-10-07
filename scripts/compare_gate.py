#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""검증 게이트가 값어치가 있는지 숫자로 잰다 (6회차).

같은 문서, 같은 질문, 같은 검색 방식. 다른 것은 인제스천뿐이다.
  게이트 ON  : 파서 라우팅 + 표 페이지 교체 + 재추출 + OCR 캐시
  게이트 OFF : pdfplumber 로 한 번 뽑고 끝

"인제스천 품질에 시간을 쓸 값어치가 있는가"에 대한 답이다.

    python scripts/compare_gate.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from finrag.eval import harness                      # noqa: E402
from finrag.parsing.metadata import load_documents   # noqa: E402
from finrag.settings import get_settings             # noqa: E402
from pipelines import baseline                       # noqa: E402


def evidence_loss() -> dict:
    """골든 근거가 게이트 OFF 청크에서 몇 건이나 사라지는가.

    Recall 보다 이쪽이 더 분명하다. 근거가 아예 없으면 어떤 검색기를 써도 못 찾는다.
    """
    s = get_settings()
    docs = load_documents()
    sq = lambda x: re.sub(r"\s+", "", x)                        # noqa: E731
    off: dict[str, list[str]] = {}
    path = s.chunks_dir / "chunks_gate_off.jsonl"
    for l in path.open(encoding="utf-8"):
        c = json.loads(l)
        off.setdefault(c["doc_id"], []).append(sq(c["text"]))

    lost, total = [], 0
    for fn, key in (("seed_golden.jsonl", "gold"), ("calc_golden.jsonl", "basis")):
        for l in (s.golden_dir / fn).open(encoding="utf-8"):
            if not l.strip():
                continue
            r = json.loads(l)
            for span in r.get(key, []):
                if docs[span["doc_id"]].format != "pdf":
                    continue
                total += 1
                if not any(sq(span["quote"]) in t for t in off.get(span["doc_id"], [])):
                    lost.append({"id": r["id"], "doc_id": span["doc_id"],
                                 "quote": span["quote"][:40]})
    return {"total": total, "lost": len(lost), "detail": lost}


def main() -> int:
    s = get_settings()
    print("=" * 60)
    print("검증 게이트 ON/OFF 비교")
    print("=" * 60)

    ev = evidence_loss()
    print(f"\n1) 골든 근거 보존  (PDF 근거 {ev['total']}건 기준)")
    print(f"   게이트 ON : {ev['total']}건 모두 청크 안에 있음")
    print(f"   게이트 OFF: {ev['total'] - ev['lost']}건 남음, {ev['lost']}건 사라짐")
    for d in ev["detail"]:
        print(f"     - {d['id']} {d['doc_id']}: “{d['quote']}”")

    print(f"\n2) 같은 질문·같은 검색기로 Recall 재측정")
    # 게이트 ON 은 이미 results/baseline.json 에 있다. 다시 돌리지 않는다.
    # (16GB 노트북에서 두 번 돌리면 스왑이 터진다)
    on_path = s.results_dir / "baseline.json"
    if on_path.exists():
        on = json.loads(on_path.read_text(encoding="utf-8"))
        print("   게이트 ON: results/baseline.json 재사용")
    else:
        on = harness.run(baseline.build(), "gate_on")
    off_pipe = baseline.build()

    # 컬렉션만 바꿔 같은 파이프라인을 다시 돌린다.
    from finrag.retrieval import dense
    orig = dense.search

    def patched(q, k=10, flt=None, collection=None):
        return orig(q, k=k, flt=flt, collection=f"{s.qdrant_collection}_gate_off")

    dense.search = patched
    try:
        off = harness.run(off_pipe, "gate_off")
    finally:
        dense.search = orig

    print(f"\n{'':16}{'게이트 ON':>12}{'게이트 OFF':>12}{'차이':>10}")
    print("-" * 50)
    for m in ("recall@1", "recall@5", "recall@10", "mrr"):
        a, b = on["overall"][m], off["overall"][m]
        print(f"{m:16}{a:>12.1%}{b:>12.1%}{(a - b) * 100:>+9.1f}%p")

    out = s.results_dir / "gate_comparison.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"evidence": ev, "gate_on": on["overall"],
                               "gate_off": off["overall"],
                               "by_type": {"gate_on": on["by_type"], "gate_off": off["by_type"]}},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n→ {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
