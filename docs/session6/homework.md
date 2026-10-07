# 6회차 과제

필수 둘, 선택 하나입니다. 다음 회차 전까지 냅니다. 끝났는지는 `make check-s06` 가 **5/5** 인지로 압니다. 30분 안쪽입니다.

## 필수 1. 수업에서 만든 결과 파일을 커밋 — 수업에서 끝냈으면 5분

채울 자리 둘(`metrics.aggregate`, `judge.agreement`)이 채워졌으면 이렇게 끝납니다.

```bash
make test             # 116개 전부 통과
make compare          # results/compare.csv
make judge            # results/judge.json (1~2분)
make calc-e2e         # results/calc_e2e.json (약 5분)
make check-s06        # 4/5. 마지막 항목은 필수 2 입니다
```

Windows 는 [install.md](../install.md) 의 PowerShell 명령을 씁니다. 수업에서 못 채운 함수가 있으면 강사가 수업 뒤 올리는 **solution 브랜치**를 봅니다.

https://github.com/hyeonsikseo/finance-agentic-rag-s06/tree/solution/src/finrag

보고 베끼는 게 아니라 **읽고 닫은 다음 자기 손으로 다시 씁니다.**

## 필수 2. ROI 1쪽 — 20분

"이 시스템이 한 달에 얼마이고, 무엇을 아끼는가"를 **한 쪽**으로 씁니다. 숫자는 `make roi` 가 찍어 줍니다. 이 문서가 하는 일은 측정값과 가정값을 **구분해서** 적는 것입니다.

1. `docs/templates/roi.md` 를 `docs/roi.md` 로 복사합니다.
2. 빈칸(`____`)을 전부 채웁니다. `make check-s06` 가 빈칸이 남았는지 셉니다.

채울 때 볼 것:

- **1절 측정값**은 `make roi` 의 "측정값" 부분을 그대로 옮기고 출처에 파일 이름(`results/agentic.json`)을 적습니다. "어느 호출이 큰지 한 줄"은 모델별 토큰에서 읽습니다(답변을 만드는 mini 의 출력 토큰이 보통 가장 비쌉니다).
- **2절 가정값**은 기본값을 그대로 써도 됩니다. 그래도 "왜 그 값인가" 칸은 채웁니다. 일 질문 수는 1회차 디스커버리 노트의 현재 상담 건수가 있으면 그것으로.
- **4절 TCO** 는 `make roi` 의 표 두 줄과 "손익이 뒤집히는 일 질문 수"입니다. 가정을 바꾸면 `python scripts/roi.py --daily 2000` 처럼 다시 돌려 둘을 비교해 봐도 좋습니다.
- **6절 "이 숫자를 믿기 전에 3줄"**이 가장 중요합니다. 템플릿의 예시 셋을 자기 말로 바꿔 적습니다. 오거절률은 `results/agentic.json` 의 `false_refusal_rate` 입니다.

길이는 한 쪽. 완성 예시는 과제 마감 뒤 `docs/session6/examples/` 에 올립니다.

## 선택. 평가 리포트 — 15분

`docs/eval_report.md` 를 새로 만들어 셋을 적습니다. (1) `make compare` 의 유형별 표에서 어디가 올랐고 어디가 내려갔는지 **세 줄**. 전체 평균이 아니라 유형 이름으로. (2) `results/judge_calibration.json` 에서 judge 와 사람이 가장 어긋난 문항 하나를 골라 왜 어긋났는지 한 줄(어느 항목이, judge 가 후했나 박했나). (3) `results/calc_e2e.json` 에서 틀린 문항 하나를 골라 함수가 틀렸는지 추출이 틀렸는지 한 줄. 8회차 readout 의 성능 절이 이 세 줄로 시작합니다.

## 제출

**마감: 10월 12일(월) 밤.** 7회차(10월 13일 화 21:00)에서 `/ask` API 의 응답 시간 예산에 오늘 잰 p95 와 문항당 비용이 들어갑니다.

1. `make check-s06` 가 5/5 인지 봅니다.
2. 커밋하고 자기 포크에 올립니다.

```bash
git add src/finrag/eval/metrics.py src/finrag/eval/judge.py results/compare.csv results/judge.json results/judge_calibration.json results/calc_e2e.json results/filter_accuracy.json results/roi.json results/check_s06.json docs/roi.md
git commit -m "6회차 과제"
git push
```

3. 자기 포크 URL(`https://github.com/<계정>/finance-agentic-rag-s06`)를 디스코드에 올립니다. 포크 없이 받았으면 위 파일들을 zip 으로 묶어 올립니다. `.env` 는 올리지 않습니다(커밋되지 않게 되어 있습니다).

## check-s06 가 보는 것

| 항목 | 통과 기준 |
|---|---|
| 3단계 비교표 | `results/compare.csv` 에 baseline · hybrid · agentic 열이 있다 |
| 오거절률 · 미답변 정확도 행 | 같은 파일에 `false_refusal_rate` 와 `abstain_accuracy` 행이 있다 |
| judge 20문항 | `results/judge.json` 에 20문항이 있고 가짜 모델이 아니다 |
| 계산 정확도 기록 | `results/calc_e2e.json` 에 15문항이 있다 |
| ROI 문서 | `docs/roi.md` 가 있고 빈칸(`____`)이 없다 |

## 마감 뒤 강사가 올리는 것

`docs/session6/examples/` 에 ROI 1쪽 완성본과 평가 리포트 예시를 올립니다. 받는 법은 같습니다.

```bash
git pull upstream main
```

## 7회차 전에 하나

7회차는 API 셋(API · Qdrant · UI)을 `docker compose up` 한 줄로 띄웁니다. **Docker Desktop** 이 설치되어 있고 `docker --version` 이 찍히는지만 확인해 두세요. 설치 안내는 7회차 레포지토리에 넣습니다.
