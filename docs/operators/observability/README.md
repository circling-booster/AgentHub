# Observability Guide

AgentHub 모니터링 및 로깅 설정 가이드입니다.

---

## Logging Configuration

### Log Levels

AgentHub는 Python 표준 로깅을 사용합니다:

| Level | Description | Use Case |
|-------|-------------|----------|
| `DEBUG` | 상세 디버그 정보 | 개발/디버깅 |
| `INFO` | 일반 운영 정보 | 프로덕션 기본값 |
| `WARNING` | 경고 메시지 | 주의 필요 상황 |
| `ERROR` | 에러 정보 | 오류 발생 |

### Log Format

**configs/default.yaml:**
```yaml
observability:
  log_llm_requests: true
  max_log_chars: 500
  log_format: "text"  # "text" | "json"
```

### Text Format (기본)

```
2026-02-05 10:30:15 - src.adapters - INFO - LLM call success: model=gpt-4o tokens=150 duration=1200ms
```

### JSON Format

```json
{
  "timestamp": "2026-02-05T01:30:15.123456+00:00",
  "level": "INFO",
  "logger": "src.adapters.outbound.adk.litellm_callbacks",
  "message": "LLM call success: model=gpt-4o tokens=150 duration=1200ms"
}
```

JSON 포맷은 외부 로그 수집 시스템(ELK, Datadog 등)과 통합 시 유용합니다.

---

## LLM Call Tracking

AgentHub는 모든 LLM API 호출을 자동으로 추적합니다.

### Tracked Metrics

| Metric | Description | Example |
|--------|-------------|---------|
| **model** | 사용된 LLM 모델 | `openai/gpt-4o-mini` |
| **tokens** | 총 토큰 수 | `250` |
| **prompt_tokens** | 입력 토큰 | `100` |
| **completion_tokens** | 출력 토큰 | `150` |
| **duration_ms** | 응답 시간 (ms) | `1200` |
| **cost_usd** | 예상 비용 (USD) | `0.0025` |

### Success Log

```
LLM call success: model=openai/gpt-4o-mini tokens=250 duration=1200ms
```

### Failure Log

```
LLM call failed: model=openai/gpt-4o-mini error=RateLimitError
```

---

## Tool Call Tracking

MCP 도구 호출도 추적됩니다.

### Tracked Events

| Event | Description |
|-------|-------------|
| `tool_call` | 도구 호출 시작 |
| `tool_result` | 도구 실행 결과 |
| `agent_transfer` | A2A 에이전트 전환 |

### Tool Call API

대화의 도구 호출 기록 조회:

```bash
curl -H "X-Extension-Token: <token>" \
  http://localhost:8000/api/conversations/{id}/tool-calls
```

**응답 예시:**
```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {"query": "weather"},
      "result": "Sunny, 22°C",
      "duration_ms": 350
    }
  ]
}
```

---

## Cost Tracking (Phase 6)

Phase 6에서 추가된 비용 추적 및 예산 관리 기능입니다.

### Configuration

**configs/default.yaml:**
```yaml
cost:
  monthly_budget_usd: 100.0
  warning_threshold: 0.9     # 90%: 경고
  critical_threshold: 1.0    # 100%: 심각
  hard_limit_threshold: 1.1  # 110%: API 차단
```

**환경변수 오버라이드:**
```bash
export COST__MONTHLY_BUDGET_USD=200.0
export COST__WARNING_THRESHOLD=0.8
```

### Usage Entity

각 LLM 호출마다 사용량이 자동으로 기록됩니다:

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | LLM 모델명 (예: `openai/gpt-4o-mini`) |
| `prompt_tokens` | int | 입력 토큰 수 |
| `completion_tokens` | int | 출력 토큰 수 |
| `total_tokens` | int | 총 토큰 수 |
| `cost_usd` | float | 비용 (USD) |
| `created_at` | datetime | 기록 시간 |

### Budget Alert System

예산 사용률에 따른 경고 단계:

| Alert Level | Usage % | can_proceed | Action |
|-------------|---------|-------------|--------|
| `safe` | < 90% | ✅ | 정상 운영 |
| `warning` | 90-100% | ✅ | 경고 로그 출력, Extension 알림 |
| `critical` | 100-110% | ⚠️ | 심각 경고, 주의 필요 |
| `blocked` | > 110% | ❌ | API 호출 차단 (BudgetExceededError) |

### Budget Status Response

```json
{
  "monthly_budget": 100.0,
  "current_spending": 92.50,
  "usage_percentage": 92.5,
  "alert_level": "warning",
  "can_proceed": true
}
```

---

## Usage API Endpoints

### 월간 사용량 요약

```bash
curl -H "X-Extension-Token: <token>" \
  http://localhost:8000/api/usage/summary
```

**Response:**
```json
{
  "total_cost": 45.50,
  "total_tokens": 350000,
  "call_count": 1250,
  "by_model": {
    "openai/gpt-4o-mini": 30.25,
    "openai/gpt-4o": 15.25
  }
}
```

### 모델별 사용량

```bash
curl -H "X-Extension-Token: <token>" \
  http://localhost:8000/api/usage/by-model
```

### 예산 상태 조회

```bash
curl -H "X-Extension-Token: <token>" \
  http://localhost:8000/api/usage/budget
```

### 예산 업데이트

```bash
curl -X PUT \
  -H "X-Extension-Token: <token>" \
  -H "Content-Type: application/json" \
  -d '{"monthly_budget_usd": 150.0}' \
  http://localhost:8000/api/usage/budget
```

**상세 API 스펙:** [../../developers/architecture/api/endpoints/usage.md](../../developers/architecture/api/endpoints/usage.md)

---

## Debug Tips

### 1. 로그 레벨 상향

개발 중 상세 로그 확인:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### 2. 토큰 사용량 모니터링

비용 효율적인 운영을 위해:
- `max_log_chars` 조정으로 로그 크기 제한
- 월간 예산 알림 활성화
- 모델별 토큰 사용량 분석

### 3. 외부 시스템 통합

JSON 로그 포맷 사용 시:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- Grafana Loki

---

## Related

- [../](../) - Operators Hub
- [../deployment/](../deployment/) - 배포 가이드
- [../security/](../security/) - 보안 설정
- [../../developers/testing/](../../developers/testing/) - 테스트 디버그
