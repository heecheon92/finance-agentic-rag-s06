# 약관부터 답변까지 — 6회차

금융 문서 특화 Agentic RAG 수업의 6회차 레포지토리입니다. 5회차 레포지토리(finance-agentic-rag-s05)와는 별개이고 새로 받습니다. 1~5회차 내용은 그대로 들어 있고, 5회차에 채운 자리 넷(`grade` · `route_after_grade`, `extract_filters`, `savings_early_termination_rate`)은 **강사가 작성한 코드로 채워져** 있습니다. 자기 코드로 바꿔 써도 됩니다.

## 6회차에 할 일

1. 설치합니다. 5회차 폴더에서 문서·청크·모델·결과 파일·`.env` 를 복사합니다. 새로 받는 것도, 새 패키지도 없습니다. → [docs/install.md](docs/install.md)
2. 수업 앞부분은 노트북으로 결과 파일 셋을 읽고(같은 40문항, 같은 gold), 지표 다섯의 분모를 봅니다. → `make notebook`
3. 수업 중반은 채울 자리 둘(`metrics.aggregate`, `judge.agreement`)을 채우고, 3단계 표(`make compare`)와 judge 일치도(`make judge-calibrate`)를 읽습니다. → [docs/session6/lab.md](docs/session6/lab.md)
4. 수업 뒷부분은 계산 정확도(`make calc-e2e`) · 미답변과 오거절 · 적대적 · 필터 정확도(`make filter-accuracy`) · 게이트 ON/OFF 를 숫자로 보고, 마지막에 돈으로 바꿉니다(`make roi`).
5. 과제는 필수 둘(결과 파일 커밋, ROI 1쪽)에 선택 하나이고, `make check-s06` 가 5/5 이면 끝입니다. → [docs/session6/homework.md](docs/session6/homework.md)

## 폴더

| 폴더 | 무엇 |
|---|---|
| `docs/install.md` | 설치. 5회차 폴더에서 복사하는 단계 |
| `docs/session6/` | 실습 순서(lab.md)와 과제(homework.md) |
| `docs/templates/roi.md` | 과제 "ROI 1쪽"의 템플릿. `docs/roi.md` 로 복사해 채웁니다 |
| `docs/session5/examples/` | 5회차 과제(에이전트 정책 1쪽)의 강사 완성본 |
| `notebooks/s06_eval.ipynb` | 평가 분석 20분. 수업 1~2부. Qdrant 를 열지 않습니다 |
| `src/finrag/eval/metrics.py` | 지표. 채울 것 `aggregate`(실습 1)가 여기 있습니다 |
| `src/finrag/eval/judge.py` | LLM-as-Judge. 루브릭과 채점은 완성본, 채울 것 `agreement`(실습 2) |
| `src/finrag/eval/report.py`, `cost.py`, `filters_eval.py` | 3단계 표, 토큰 → 비용, 필터 정확도. 읽기만 합니다 |
| `src/finrag/eval/harness.py` | 3회차부터 같은 하네스. 결과 행에 `usage` · `filters` · `chunk_ids` · `calc` 가 들어갑니다 |
| `scripts/judge_run.py`, `calc_e2e.py`, `filter_accuracy.py`, `roi.py` | 오늘의 측정 넷 |
| `scripts/compare_gate.py`, `make_snapshot.py` | 검증 게이트 ON/OFF 비교(강사 시연. 선택) |
| `data/golden/judge_calibration.jsonl` | 강사 답변 17개(20문항 중 답한 것)와 강사 라벨. judge 일치도의 기준 |
| `tests/test_metrics.py`, `tests/test_judge.py` | 채운 것이 맞는지 보는 테스트. 2~5회차 테스트도 그대로 돕니다 |
| `scripts/check_session.py` | 6회차 확인. 결과 파일이 제출물입니다 |

## 명령

```bash
make setup            # 패키지 설치. 5회차 폴더가 있으면 1분
make index            # 청크를 Qdrant 에 넣는다 (스냅샷 재사용). 10초
make notebook         # 평가 노트북 열기
make test             # 자동 채점. 2~5회차 102개 + 6회차 14개. 채우기 전에는 11개 실패가 정상입니다
make compare          # 결과 파일 셋을 한 표로 → results/compare.csv (실습 1 뒤에 됩니다)
make judge-calibrate  # 강사 답변 17개를 judge 로 채점해 강사 라벨과 일치도. 1~2분
make judge            # 자기 답변 20문항을 judge 로 채점 → results/judge.json. 1~2분
make calc-e2e         # 계산 골든셋 15문항을 에이전트로 → results/calc_e2e.json. 약 5분. 휴식에
make filter-accuracy  # Self-Query 필터 정확도 → results/filter_accuracy.json. 1초
make roi              # 토큰 → 문항당 비용 → 월 비용 · 3년 TCO → results/roi.json. 1초
make check-s06        # 결과물이 조건 5개를 만족하는지 확인 → results/check_s06.json
```

Windows 에서는 `make` 가 없으니 [docs/install.md](docs/install.md) 의 PowerShell 명령을 씁니다.

## 원본 문서가 레포지토리에 없는 이유

약관과 상품설명서는 각 금융회사의 저작물이라 다시 나눠 줄 수 없습니다. 레포지토리에는 "무엇을 어디서 받는지"만 있고, 각자 원 출처에서 받거나 5회차 폴더에서 복사합니다. 자세한 것은 [data/README.md](data/README.md) 에 있습니다. 같은 이유로 문서 본문이 들어 있는 `data/chunks/`, `data/ocr_cache/`, `data/bm25_cache/` 도 레포지토리에 올리지 않습니다.
