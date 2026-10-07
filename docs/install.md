# 설치와 준비물 받기 (6회차)

5회차와 같은 컴퓨터에서, 5회차 폴더(`finance-agentic-rag-s05`) 옆에 새 레포지토리를 받습니다. **새로 받는 것도, 새 패키지도 없습니다.** 문서·청크·모델·결과 파일·`.env` 를 5회차 폴더에서 복사하면 끝입니다. 10분 안쪽입니다. 수업 전날까지 끝내 두고, 마지막 6번의 확인 줄 둘을 디스코드에 남겨 주세요.

## 1. 준비물 두 가지, git 과 uv

1~5회차에 했으면 건너뜁니다. 확인은 `git --version`, `uv --version`.

## 2. 레포지토리 받기

지난 회차처럼 포크를 먼저 합니다.

1. 브라우저에서 https://github.com/hyeonsikseo/finance-agentic-rag-s06 를 열고 오른쪽 위 **Fork** 를 누릅니다.
2. 그 레포지토리를 받습니다. `<계정>` 자리에 자기 GitHub 계정을 넣습니다.

```bash
git clone https://github.com/<계정>/finance-agentic-rag-s06.git
cd finance-agentic-rag-s06
git remote add upstream https://github.com/hyeonsikseo/finance-agentic-rag-s06.git
```

포크가 막히면 원본을 그대로 받고 과제는 zip 으로 냅니다.

## 3. 5회차 폴더에서 가져오기

문서, OCR 캐시, 청크, 임베딩 스냅샷, BM25 캐시, 모델, **결과 파일 넷**(baseline · hybrid · agentic · adversarial), 그리고 `.env`(키) 를 복사합니다. 폴더가 다른 곳에 있으면 경로만 바꿉니다.

**Mac**

```bash
cp -R ../finance-agentic-rag-s05/data/raw data/
cp -R ../finance-agentic-rag-s05/data/ocr_cache data/
cp -R ../finance-agentic-rag-s05/data/chunks data/
cp ../finance-agentic-rag-s05/data/ingest_report.json data/
cp -R ../finance-agentic-rag-s05/data/embeddings data/
cp -R ../finance-agentic-rag-s05/data/bm25_cache data/
cp -R ../finance-agentic-rag-s05/models .
mkdir -p results && cp ../finance-agentic-rag-s05/results/baseline.json ../finance-agentic-rag-s05/results/hybrid.json ../finance-agentic-rag-s05/results/agentic.json ../finance-agentic-rag-s05/results/adversarial.json results/
cp ../finance-agentic-rag-s05/.env .env
```

**Windows (PowerShell)**

```powershell
Copy-Item -Recurse ..\finance-agentic-rag-s05\data\raw data\
Copy-Item -Recurse ..\finance-agentic-rag-s05\data\ocr_cache data\
Copy-Item -Recurse ..\finance-agentic-rag-s05\data\chunks data\
Copy-Item ..\finance-agentic-rag-s05\data\ingest_report.json data\
Copy-Item -Recurse ..\finance-agentic-rag-s05\data\embeddings data\
Copy-Item -Recurse ..\finance-agentic-rag-s05\data\bm25_cache data\
Copy-Item -Recurse ..\finance-agentic-rag-s05\models .
New-Item -ItemType Directory -Force results | Out-Null
Copy-Item ..\finance-agentic-rag-s05\results\baseline.json, ..\finance-agentic-rag-s05\results\hybrid.json, ..\finance-agentic-rag-s05\results\agentic.json, ..\finance-agentic-rag-s05\results\adversarial.json results\
Copy-Item ..\finance-agentic-rag-s05\.env .env
```

`models` 는 4GB 가 넘어서 1~2분 걸립니다. 디스크가 빠듯하면 복사 대신 옮겨도 됩니다(`mv`, `Move-Item`). 5회차 폴더는 이제 쓰지 않습니다.

**`results/agentic.json` 이 오늘의 재료입니다.** 5회차 과제(`make agentic`)를 아직 안 돌렸으면 5회차 폴더에서 먼저 돌리고(약 12분, 키 필요) 복사합니다. 키 없이 돌린 파일(`"llm": "fake"`)은 답변률·judge·비용이 전부 의미가 없으니 키를 넣고 다시 돌립니다. 5회차 폴더가 없으면 이 폴더에서 `make download` · `make models` · `make models-rerank` · `make embeddings` · `make ingest`(약 6분) · `make baseline` · `make hybrid`(약 8분) · `make agentic`(약 12분) · `make adversarial` 을 순서대로 합니다.

## 4. 파이썬과 패키지 설치

**Mac**

```bash
make setup
```

**Windows (PowerShell)**

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

5회차와 같은 패키지입니다. 1분이면 끝납니다.

## 5. 인덱스 만들기

5회차 청크를 이 폴더의 Qdrant 에 넣습니다. 스냅샷을 재사용해서 10초입니다. 오늘 `make calc-e2e`(계산 15문항을 에이전트로)가 검색을 하므로 필요합니다.

**Mac**

```bash
make index
```

**Windows (PowerShell)**

```powershell
$env:HF_HOME = ".\models"
.venv\Scripts\python scripts\build_index.py
```

## 6. 되는지 확인

**Mac**

```bash
make test
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\python -m pytest -q
```

지금은 **실패가 정상**입니다. 채울 자리 둘이 비어 있어서 6회차 테스트 11개가 `NotImplementedError` 로 실패합니다. 마지막 줄이 `11 failed, 105 passed` 이고 `error` 가 없으면 설치는 된 것입니다. 그리고 `results/agentic.json` 을 열어 `overall` 의 `mrr` 을 봅니다. **이 마지막 줄과 그 `mrr` 값, 둘을 디스코드에 적어 주세요.**

## 막힐 때

| 증상 | 이유 | 이렇게 합니다 |
|---|---|---|
| `uv: command not found` | 설치 뒤 터미널을 새로 안 열었습니다 | 터미널을 닫고 새로 엽니다 |
| `make test` 가 `ModuleNotFoundError` | `make setup` 을 안 했습니다 | 4번 |
| `results/agentic.json` 이 없다 | 5회차 과제 필수 1 을 안 돌렸습니다 | 5회차 폴더에서 `make agentic`(12분) 뒤 3번의 복사 |
| `agentic.json` 에 `"warning"` 이 있다 | 키 없이 돌린 파일입니다 | 5회차 폴더의 `.env` 에 키를 넣고 `make agentic` 다시 |
| `make roi` 가 "usage 가 없습니다" | 10/8 이전 코드로 돌린 파일입니다 | 5회차 폴더에서 `git pull upstream main` 뒤 `make agentic` 다시. 수업 중에는 강사 값으로 진행 |
| `make compare` 가 `NotImplementedError` | 실습 1 을 아직 안 채웠습니다. 정상 | 수업에서 채웁니다 |
| `make index` 가 느리다 | 스냅샷(`data/embeddings`)을 안 복사했습니다 | 3번 |
