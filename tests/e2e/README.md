# E2E 테스트 실행 가이드

Playwright 기반 E2E 테스트 실행 방법 및 문제 해결 가이드입니다.

---

## 실행 전 체크리스트

### 1. 기존 서버 종료

E2E 테스트는 자체적으로 서버를 시작하므로, 기존 실행 중인 서버를 종료해야 합니다.

**Windows:**
```bash
# 포트 8000 사용 중인 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료
taskkill //F //PID <PID>
```

**Linux/macOS:**
```bash
# 포트 8000 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

### 2. Playwright 브라우저 설치 확인

```bash
# Playwright 브라우저가 없으면 설치
playwright install chromium
```

---

## 테스트 실행

### 전체 E2E 테스트 실행

```bash
pytest tests/e2e/test_playground.py -m e2e_playwright -v --timeout=120
```

**옵션 설명:**
- `-m e2e_playwright`: E2E Playwright 테스트만 실행
- `-v`: 상세 출력 (테스트 이름 표시)
- `--timeout=120`: 테스트 타임아웃 120초 (서버 시작 시간 포함)

### 개별 테스트 클래스 실행

```bash
# MCP 관리 테스트만 실행
pytest tests/e2e/test_playground.py::TestPlaygroundMcpManagement -v -m e2e_playwright

# Chat 스트리밍 테스트만 실행
pytest tests/e2e/test_playground.py::TestPlaygroundChatStreaming -v -m e2e_playwright
```

### Headed 모드 실행 (디버깅)

```bash
# 브라우저 UI를 보면서 실행
pytest tests/e2e/test_playground.py -m e2e_playwright -v --headed
```

---

## 테스트 격리 원칙

E2E 테스트는 **테스트 간 독립성**을 보장하기 위해 다음 원칙을 따릅니다:

### 1. clean_state Fixture

각 테스트는 `clean_state` fixture에 의해 전후로 초기화됩니다:

```python
@pytest.fixture
def clean_state(backend_url: str):
    """각 테스트 전후 상태 초기화"""
    import httpx

    def _reset():
        httpx.post(f"{backend_url}/test/reset-data", timeout=10.0)

    _reset()  # Setup
    yield
    _reset()  # Teardown
```

### 2. DEV_MODE 전용 API

`/test/reset-data` 엔드포인트는 DEV_MODE에서만 활성화됩니다:
- MCP 서버 전체 해제
- A2A 에이전트 전체 해제
- 대화 전체 삭제

**보안 주의:**
- 프로덕션 환경에서는 절대 DEV_MODE=true 사용 금지
- 로컬 개발 환경에서만 사용

### 3. Module Scope Fixture

`backend_server`, `static_server` fixture는 module scope로 실행:
- 모든 테스트가 동일한 서버 인스턴스 공유
- 테스트 시작 시 1회만 서버 시작
- 테스트 종료 시 서버 자동 종료

---

## 실패 시 Cleanup

테스트 실패 후 서버가 남아있으면 다음 테스트 실행이 실패할 수 있습니다.

### 서버 강제 종료 후 재실행

**Windows:**
```bash
# 1. 포트 8000, 3000 사용 중인 프로세스 확인 및 종료
netstat -ano | findstr :8000
taskkill //F //PID <PID>

netstat -ano | findstr :3000
taskkill //F //PID <PID>

# 2. 테스트 재실행
pytest tests/e2e/test_playground.py -m e2e_playwright -v
```

**Linux/macOS:**
```bash
# 1. 포트 8000, 3000 사용 중인 프로세스 확인 및 종료
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# 2. 테스트 재실행
pytest tests/e2e/test_playground.py -m e2e_playwright -v
```

---

## 트러블슈팅

### 1. "Address already in use" 오류

**원인:** 포트 8000 또는 3000이 이미 사용 중

**해결:**
```bash
# 실행 전 체크리스트 > 1. 기존 서버 종료 참고
```

### 2. "Timeout waiting for health check"

**원인:** 서버 시작 지연 또는 실패

**해결:**
1. 로그 확인:
   ```bash
   pytest tests/e2e/test_playground.py -m e2e_playwright -v -s
   ```
2. 수동으로 서버 시작 후 health 확인:
   ```bash
   DEV_MODE=true uvicorn src.main:app --host localhost --port 8000
   curl http://localhost:8000/health
   ```

### 3. "14/18 tests failed" (테스트 격리 실패)

**원인:** 이전 버전에서는 cleanup이 불완전했음

**해결:**
- 현재 버전은 `clean_state` fixture로 자동 초기화됨
- 문제가 계속되면 수동으로 reset:
  ```bash
  curl -X POST http://localhost:8000/test/reset-data
  ```

### 4. Playwright 브라우저 미설치

**원인:** Chromium 브라우저가 설치되지 않음

**해결:**
```bash
playwright install chromium
```

---

## 예상 결과

성공적인 실행 시:
```
========================= 17 passed in 45.23s =========================
```

**Note:**
- 일부 테스트는 skip될 수 있음 (예: Health Check Failure 테스트)
- 개별 실행과 전체 실행 결과가 동일해야 함 (테스트 격리 성공)

---

## CI/CD 통합

GitHub Actions에서 E2E 테스트 실행:

```yaml
- name: Run E2E Tests
  env:
    DEV_MODE: true
  run: |
    pytest tests/e2e/test_playground.py -m e2e_playwright -v --timeout=120
```

---

## 관련 문서

- [../README.md](../README.md) - 전체 테스트 전략
- [test_playground.py](test_playground.py) - E2E 테스트 코드
- [../../docs/project/planning/active/08_playground/06_e2e_tests.md](../../docs/project/planning/active/08_playground/06_e2e_tests.md) - Phase 6 계획

---

*Last Updated: 2026-02-05*
*Version: 1.0 (clean_state fixture 기반)*
