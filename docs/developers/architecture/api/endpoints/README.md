# API Endpoint Specifications

AgentHub REST API 엔드포인트 상세 스펙 문서입니다.

---

## Endpoint Groups

| Group | Base Path | Description | Spec |
|-------|-----------|-------------|------|
| **Usage** | `/api/usage/*` | 비용 추적 및 예산 관리 | [usage.md](./usage.md) |

---

## Common Patterns

### Authentication

모든 `/api/*` 엔드포인트는 Extension Token 인증이 필요합니다:

```bash
curl -H "X-Extension-Token: <token>" http://localhost:8000/api/usage/summary
```

### Error Response

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | 성공 |
| `400` | 잘못된 요청 |
| `401` | 인증 필요 |
| `403` | 토큰 불일치 |
| `404` | 리소스 없음 |
| `422` | 유효성 검증 실패 |

---

## Related

- [../](../) - API Architecture Overview
- [../../../guides/implementation/](../../../guides/implementation/) - 구현 가이드

---

*Last Updated: 2026-02-05*
