# Deployment Guide

AgentHub 설치 및 배포 절차 가이드입니다.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.10+ | 3.12 권장 |
| **Node.js** | 18+ | Extension 빌드용 |
| **Git** | 2.30+ | 저장소 클론 |
| **Chrome** | 120+ | Manifest V3 지원 |

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/user/agenthub.git
cd agenthub
```

### 2. Python Environment

```bash
# 가상환경 생성
python -m venv .venv

# 활성화 (Windows)
.venv\Scripts\activate

# 활성화 (macOS/Linux)
source .venv/bin/activate

# 의존성 설치
pip install -e ".[dev]"
```

### 3. Extension Dependencies

```bash
cd extension
npm install
cd ..
```

---

## Configuration

### Settings Hierarchy

AgentHub는 계층적 설정 시스템을 사용합니다:

```
환경변수 > .env > configs/default.yaml > 기본값
```

### .env 설정

```bash
# 템플릿 복사
cp .env.example .env
```

**.env 주요 항목:**

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API 키 | `sk-ant-...` |
| `OPENAI_API_KEY` | GPT API 키 | `sk-...` |
| `GOOGLE_API_KEY` | Gemini API 키 | `AIza...` |
| `SERVER__PORT` | 서버 포트 | `8000` |
| `LLM__DEFAULT_MODEL` | 기본 LLM 모델 | `openai/gpt-4o-mini` |

### configs/default.yaml

서버 기본 설정 파일:

```yaml
server:
  host: localhost
  port: 8000

llm:
  default_model: "openai/gpt-4o-mini"
  timeout: 120

storage:
  data_dir: "./data"
  database: "agenthub.db"

mcp:
  max_active_tools: 100
  cache_ttl_seconds: 300

gateway:
  rate_limit_rps: 5.0
  circuit_failure_threshold: 5

cost:
  monthly_budget_usd: 100.0
  warning_threshold: 0.9
```

환경변수로 중첩 설정 오버라이드:
- `SERVER__HOST=0.0.0.0`
- `LLM__TIMEOUT=180`

### Gateway Settings (Phase 6)

Circuit Breaker, Rate Limiting 설정:

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY__RATE_LIMIT_RPS` | `5.0` | 초당 요청 제한 (requests/second) |
| `GATEWAY__BURST_SIZE` | `10` | Token Bucket capacity (burst 허용) |
| `GATEWAY__CIRCUIT_FAILURE_THRESHOLD` | `5` | 연속 실패 임계값 (OPEN 전이) |
| `GATEWAY__CIRCUIT_RECOVERY_TIMEOUT` | `60.0` | Circuit 복구 대기 시간 (초) |
| `GATEWAY__FALLBACK_ENABLED` | `true` | Fallback 서버 전환 활성화 |

**YAML 설정:**

```yaml
gateway:
  rate_limit_rps: 5.0
  burst_size: 10
  circuit_failure_threshold: 5
  circuit_recovery_timeout: 60.0
  fallback_enabled: true
```

### Cost Settings (Phase 6)

LLM 비용 추적 및 예산 관리 설정:

| Variable | Default | Description |
|----------|---------|-------------|
| `COST__MONTHLY_BUDGET_USD` | `100.0` | 월별 예산 (USD) |
| `COST__WARNING_THRESHOLD` | `0.9` | 90%: 경고 알림 |
| `COST__CRITICAL_THRESHOLD` | `1.0` | 100%: 심각 경고 |
| `COST__HARD_LIMIT_THRESHOLD` | `1.1` | 110%: API 호출 차단 |

**YAML 설정:**

```yaml
cost:
  monthly_budget_usd: 100.0
  warning_threshold: 0.9
  critical_threshold: 1.0
  hard_limit_threshold: 1.1
```

**참조:** `src/config/settings.py` (61-78줄)

---

## Running the Server

### Development Mode

```bash
uvicorn src.main:app --host localhost --port 8000 --reload
```

`--reload`: 코드 변경 시 자동 재시작

### Production Mode

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

| Flag | Description |
|------|-------------|
| `--host 0.0.0.0` | 외부 접근 허용 |
| `--workers 4` | 워커 프로세스 수 |

---

## Building the Extension

### Development Build

```bash
cd extension
npm run dev
```

- 자동 리로드 활성화
- 코드 변경 시 실시간 반영

### Production Build

```bash
cd extension
npm run build
```

빌드 결과: `extension/.output/chrome-mv3/`

---

## Loading in Chrome

1. `chrome://extensions/` 접속
2. 우측 상단 **개발자 모드** 활성화
3. **압축해제된 확장 프로그램을 로드합니다** 클릭
4. `extension/.output/chrome-mv3` 폴더 선택
5. Extension 아이콘 확인 (Connected 표시)

---

## Health Checks

### Server Status

```bash
curl http://localhost:8000/health
```

**정상 응답:**
```json
{"status": "ok"}
```

### MCP Endpoints

```bash
curl -H "X-Extension-Token: <token>" http://localhost:8000/api/endpoints
```

### A2A Agents

```bash
curl -H "X-Extension-Token: <token>" http://localhost:8000/api/a2a/agents
```

---

## Data Directory

AgentHub는 SQLite 데이터베이스를 사용합니다:

```
./data/
├── agenthub.db       # 메인 DB (WAL 모드)
├── agenthub.db-wal   # Write-Ahead Log
└── agenthub.db-shm   # 공유 메모리
```

**권한 확인:**
```bash
# 데이터 디렉토리 생성 및 권한
mkdir -p ./data
chmod 755 ./data
```

---

## Related

- [../](../) - Operators Hub
- [../observability/](../observability/) - 모니터링 및 로깅
- [../security/](../security/) - 보안 설정
