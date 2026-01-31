# Phase 5 Part D: Test Infrastructure Enhancement (Steps 11-12)

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Part A Complete
> **목표:** 서버 시작 검증 테스트, 테스트 포트 동적 설정
> **예상 테스트:** ~5 신규
> **실행 순서:** Step 11 → Step 12
> **병렬:** Part B, Part C와 병렬 가능

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **11** | Server Startup Validation | ⬜ |
| **12** | Dynamic Test Port Configuration | ⬜ |

---

## Step 11: Server Startup Validation

**문제:** 모든 테스트 통과해도 `uvicorn src.main:app` 시작 시 import 에러, DI 설정 오류 등 발생 가능

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `tests/integration/test_app_startup.py` | NEW | FastAPI app lifespan 전체 검증 |

**검증 항목:**
- FastAPI app 인스턴스 생성 성공
- DI Container wiring 정상
- Lifespan startup/shutdown 이벤트 실행
- 모든 라우터 등록 확인 (`/api/chat`, `/api/mcp`, `/api/a2a`, `/health`)
- Settings 로딩 (YAML + .env)

**TDD 순서:**
1. RED: `test_app_creates_and_starts`
2. RED: `test_all_routers_registered`
3. RED: `test_settings_loaded`
4. GREEN: 필요 시 main.py 또는 container.py 수정
5. REFACTOR: 테스트 헬퍼 추출

**DoD:**
- [ ] 3개 startup 검증 테스트 통과
- [ ] CI에서 서버 시작 오류 조기 감지 가능

---

## Step 12: Dynamic Test Port Configuration

**문제:** MCP 테스트 서버 포트 9000, A2A 포트 9001 하드코딩

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `tests/conftest.py` | MODIFY | 동적 포트 할당 + 환경변수 오버라이드 |
| `tests/integration/adapters/conftest.py` | MODIFY | MCP_TEST_URL 동적화 |

**핵심 설계:**
```python
# tests/conftest.py
import os, socket

def get_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

@pytest.fixture(scope="session")
def a2a_test_port():
    return int(os.environ.get("A2A_TEST_PORT", get_free_port()))

@pytest.fixture(scope="session")
def mcp_test_port():
    return int(os.environ.get("MCP_TEST_PORT", "9000"))
```

**TDD 순서:**
1. RED: `test_dynamic_port_allocation`
2. RED: `test_port_env_override`
3. GREEN: conftest.py 수정

**DoD:**
- [ ] 환경변수로 테스트 포트 오버라이드 가능
- [ ] 기본값은 동적 할당 (A2A) 또는 기존 값 유지 (MCP)
- [ ] `pytest-xdist` 병렬 실행 시 포트 충돌 방지

---

## 커밋 정책

```
# 마지막에 커밋
feat(phase5): Step 11 - Server startup validation tests
feat(phase5): Step 12 - Dynamic test port configuration
docs(phase5): Part D complete - Test Infrastructure
```

---

## Part D Definition of Done

### 기능
- [ ] 서버 시작 검증 테스트 통과 (3개)
- [ ] 동적 포트 할당 동작 (2개 테스트)
- [ ] 환경변수 오버라이드 동작

### 품질
- [ ] 5+ 테스트 추가
- [ ] 기존 테스트 regression 없음

---

*Part D 계획 작성일: 2026-01-31*
