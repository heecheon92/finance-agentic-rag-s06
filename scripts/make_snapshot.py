#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""강사용 스냅샷 생성.

CPU 에서 3,700청크를 임베딩하면 약 33분 걸린다(M2, bge-m3 실측). 수강생 6명이
회차마다 이걸 다시 하면 수업이 굴러가지 않는다. 그래서 강사가 한 번 만들어 배포한다.

    python scripts/make_snapshot.py            # 임베딩 스냅샷 + Qdrant 스냅샷
    python scripts/make_snapshot.py --gate-off # 검증 게이트를 끈 비교용 컬렉션도 함께
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finrag.index import qdrant                       # noqa: E402
from finrag.index.embed import embed_chunks, snapshot_path  # noqa: E402
from finrag.settings import get_settings              # noqa: E402


def build_gate_off_chunks() -> Path:
    """게이트를 끄면 무엇이 달라지는지 보여주기 위한 대조군.

    같은 문서를 파서 라우팅·재추출·OCR 없이 기본 파서 결과 그대로 청킹한다.
    6회차에서 이 컬렉션으로 Recall 을 다시 재면 인제스천 품질의 값어치가 숫자로 나온다.
    """
    from finrag.parsing.chunk import chunk_document
    from finrag.parsing.extract import extract_with
    from finrag.parsing.metadata import load_documents

    out = get_settings().chunks_dir / "chunks_gate_off.jsonl"
    rows = []
    for meta in load_documents().values():
        path = ROOT / meta.path
        if not path.exists() or meta.format != "pdf":
            continue
        pages = extract_with(path, "pdfplumber")     # 라우팅 없음, 재시도 없음, OCR 없음
        for c in chunk_document(pages, meta):
            rows.append(c.to_dict())
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"게이트 OFF 청크 {len(rows):,}개 → {out.relative_to(ROOT)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-off", action="store_true")
    args = ap.parse_args()
    s = get_settings()

    chunks_path = s.chunks_dir / "chunks.jsonl"
    chunks = [json.loads(l) for l in chunks_path.open(encoding="utf-8") if l.strip()]
    t0 = time.perf_counter()
    vecs = embed_chunks(chunks)
    print(f"임베딩 스냅샷 {vecs.shape} ({time.perf_counter() - t0:.0f}초) → "
          f"{snapshot_path().relative_to(ROOT)}  "
          f"{snapshot_path().stat().st_size / 1e6:.0f}MB")

    if s.qdrant_url:
        # 서버 모드면 Qdrant 스냅샷 API 를 쓴다. 학생은 이걸 내려받아 복원한다.
        c = qdrant.get_client()
        snap = c.create_snapshot(collection_name=s.qdrant_collection)
        print(f"Qdrant 스냅샷: {getattr(snap, 'name', snap)}")
    else:
        # 임베디드 모드면 로컬 디렉터리를 통째로 압축한다.
        src = ROOT / s.qdrant_path
        if src.exists():
            dest = ROOT / "data" / "qdrant_snapshot"
            if dest.with_suffix(".zip").exists():
                dest.with_suffix(".zip").unlink()
            shutil.make_archive(str(dest), "zip", str(src))
            print(f"Qdrant 로컬 스냅샷 → {dest.name}.zip "
                  f"({dest.with_suffix('.zip').stat().st_size / 1e6:.0f}MB)")

    if args.gate_off:
        p = build_gate_off_chunks()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_index.py"),
                        "--chunks", str(p), "--collection", f"{s.qdrant_collection}_gate_off"],
                       check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
