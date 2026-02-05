# Usage API Specification

LLM 사용량 추적 및 예산 관리 API 상세 스펙입니다. (Phase 6 Part A Step 3)

---

## Overview

| Property | Value |
|----------|-------|
| **Base Path** | `/api/usage` |
| **Authentication** | Extension Token 필수 |
| **Source** | `src/adapters/inbound/http/routes/usage.py` |

---

## Endpoints

### GET /api/usage/summary

월별 사용량 요약을 조회합니다.

**Request:**

```bash
curl -H "X-Extension-Token: <token>" \
  http://localhost:8000/api/usage/summary
```

**Response:** `UsageSummarySchema`

```json
{
  "total_cost": 15.50,
  "total_tokens": 125000,
  "call_count": 450,
  "by_model": {
    "openai/gpt-4o-mini": 10.25,
    "openai/gpt-4o": 5.25
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_cost` | float | 총 비용 (USD) |
| `total_tokens` | int | 총 토큰 수 |
| `call_count` | int | LLM 호출 횟수 |
| `by_model` | dict | 모델별 비용 분포 |

---

### GET /api/usage/by-model

모델별 사용량을 조회합니다.

**Request:**

```bash
curl -H "X-Extension-Token: <token>" \
  http://localhost:8000/api/usage/by-model
```

**Response:** `dict[str, float]`

```json
{
  "openai/gpt-4o-mini": 10.25,
  "openai/gpt-4o": 5.25,
  "anthropic/claude-3-haiku": 2.00
}
```

---

### GET /api/usage/budget

현재 예산 상태를 조회합니다.

**Request:**

```bash
curl -H "X-Extension-Token: <token>" \
  http://localhost:8000/api/usage/budget
```

**Response:** `BudgetStatusSchema`

```json
{
  "monthly_budget": 100.0,
  "current_spending": 45.50,
  "usage_percentage": 45.5,
  "alert_level": "safe",
  "can_proceed": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `monthly_budget` | float | 월별 예산 (USD) |
| `current_spending` | float | 현재 지출 (USD) |
| `usage_percentage` | float | 사용률 (%) |
| `alert_level` | string | 경고 수준 |
| `can_proceed` | bool | API 호출 허용 여부 |

#### Alert Levels

| Level | Condition | Description |
|-------|-----------|-------------|
| `safe` | < 90% | 정상 범위 |
| `warning` | 90-100% | 예산 경고 |
| `critical` | 100-110% | 예산 초과 (허용) |
| `blocked` | > 110% | API 호출 차단 |

---

### PUT /api/usage/budget

예산 설정을 업데이트합니다.

**Request:**

```bash
curl -X PUT \
  -H "X-Extension-Token: <token>" \
  -H "Content-Type: application/json" \
  -d '{"monthly_budget_usd": 150.0}' \
  http://localhost:8000/api/usage/budget
```

**Request Body:** `UpdateBudgetRequest`

```json
{
  "monthly_budget_usd": 150.0
}
```

| Field | Type | Validation | Description |
|-------|------|------------|-------------|
| `monthly_budget_usd` | float | > 0 | 새 월별 예산 (USD) |

**Response:** `BudgetStatusSchema`

```json
{
  "monthly_budget": 150.0,
  "current_spending": 45.50,
  "usage_percentage": 30.33,
  "alert_level": "safe",
  "can_proceed": true
}
```

---

## Domain Integration

### Usage Entity

```python
@dataclass
class Usage:
    model: str              # LLM 모델명 (예: "openai/gpt-4o-mini")
    prompt_tokens: int      # 입력 토큰 수
    completion_tokens: int  # 출력 토큰 수
    total_tokens: int       # 총 토큰 수
    cost_usd: float         # 비용 (USD)
    created_at: datetime    # 생성 시간
```

### BudgetStatus Entity

```python
@dataclass
class BudgetStatus:
    monthly_budget: float     # 월 예산 (USD)
    current_spending: float   # 현재 지출 (USD)
    usage_percentage: float   # 사용률 (%)
    alert_level: str          # "safe" | "warning" | "critical" | "blocked"
    can_proceed: bool         # API 호출 허용 여부
```

---

## Related

- [./](./README.md) - Endpoint Specifications Index
- [../../../guides/implementation/](../../../guides/implementation/) - GatewayService/CostService 사용법
- [../../layer/core/](../../layer/core/) - Domain Entities

---

*Last Updated: 2026-02-05*
