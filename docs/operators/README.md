# Operators

AgentHub 운영자를 위한 가이드 허브입니다.

---

## Quick Start

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 파일에서 필요한 LLM API 키 설정

# 2. 서버 실행 (프로덕션)
uvicorn src.main:app --host 0.0.0.0 --port 8000

# 3. 헬스체크 확인
curl http://localhost:8000/health
```

---

## Sub-Sections

| Section | Description | Key Topics |
|---------|-------------|------------|
| [deployment/](deployment/) | 배포 가이드 | 설치, 설정, 빌드, 실행 |
| [observability/](observability/) | 모니터링 및 로깅 | 로그 설정, LLM 추적, 도구 호출 추적 |
| [security/](security/) | 보안 설정 | Token 인증, CORS, OAuth 2.0 |

---

## Configuration Overview

AgentHub는 계층적 설정 시스템을 사용합니다:

```
환경변수 > .env > configs/default.yaml > 기본값
```

### 주요 설정 항목

| Category | Key Settings |
|----------|--------------|
| **Server** | `host`, `port` |
| **LLM** | `default_model`, `timeout` |
| **Storage** | `data_dir`, `database` |
| **MCP** | `max_active_tools`, `cache_ttl_seconds` |
| **Gateway** | `rate_limit_rps`, `circuit_failure_threshold` |
| **Cost** | `monthly_budget_usd`, `warning_threshold` |

자세한 설정: [deployment/](deployment/)

---

## Production Checklist

### Pre-Deployment

- [ ] API 키 설정 (.env)
- [ ] 데이터 디렉토리 권한 확인
- [ ] 포트 방화벽 설정 (8000)
- [ ] CORS 허용 도메인 설정

### Post-Deployment

- [ ] `/health` 엔드포인트 응답 확인
- [ ] Extension 연결 테스트
- [ ] 로그 출력 확인
- [ ] LLM API 호출 테스트

### Monitoring

- [ ] 로그 레벨 적절히 설정 (INFO/WARNING)
- [ ] LLM 비용 추적 활성화
- [ ] 월간 예산 알림 설정

### Security

- [ ] Token 인증 활성화 확인
- [ ] CORS 설정 검증
- [ ] HTTPS 적용 (프로덕션)

---

## Health Check Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | 서버 상태 확인 |
| `/api/endpoints` | GET | 등록된 MCP 서버 목록 |
| `/api/a2a/agents` | GET | 등록된 A2A 에이전트 목록 |

---

## Related

- [../developers/](../developers/) - 개발자 가이드
- [../project/](../project/) - 프로젝트 관리
