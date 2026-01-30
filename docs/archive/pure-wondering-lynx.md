# AgentHub 프로젝트 개선 계획

**작성일:** 2026-01-29
**목적:** docs/reports 리포트 지적사항 분석 및 프로젝트 전반 개선

---

## 📊 Phase 1: 지적사항 종합 분석

### 발견된 5개 리포트:
1. **품질 평가 보고서** - Agents/Skills, TDD, 스펙 준수
2. **문서 종합 평가** - CLAUDE.md, 파일 참조, Hooks
3. **프로젝트 종합 평가** - Phase 플랜, 브랜치 전략, README
4. **Claude Code 최적화** - Hooks 전략, Skills, 2026 베스트 프랙티스
5. **종합 평가 보고서 (2026-01-29)** - 기술적 감사, CORS 버그, DI Container 누락

---

## 🔍 지적사항 분류 및 타당성 평가

### 🔴 Critical (즉시 해결 필수)

| 지적사항 | 출처 | 타당성 | 판단 근거 |
|---------|------|:-----:|----------|
| **CORS Middleware 순서 버그** | 종합평가 | ✅ **매우 타당** | FastAPI LIFO 방식 → 403 응답 시 CORS 헤더 누락 (실제 버그) |
| **DI Container 미구현** | 종합평가 | ✅ **매우 타당** | Phase 1 범위인데 `src/config/` 비어있음 → Phase 2 진입 불가 |
| **PreToolUse Hook Write-time Blocking** | 최적화 | ✅ **매우 타당** | 2026 연구: "Avoid blocking at write time" - 컨텍스트 낭비, 워크플로우 방해 |
| **folder-readme-guide.md 참조** | 문서평가 | ✅ **타당** | CLAUDE.md L158 참조 파일 없음 → **사용자 결정: CLAUDE.md 참조 제거 선호** |

**사용자 결정 사항:**
- ✅ **Phase 플랜 문서**: phase2.0.md 이미 작성됨, 검토 중
- ✅ **main 브랜치 보호**: Git pre-commit hook 추가 (SessionEnd도 병행)
- ✅ **folder-readme-guide**: 각 Phase 계획에 README 작성 포함, CLAUDE.md 참조 제거

**타당성 평가:**
- ✅ **모두 타당**: 실제 존재하는 문제, 구체적 증거 제시됨
- ✅ **우선순위 적절**: 프로젝트 진행 차단 또는 워크플로우 효율성에 직접 영향

---

### 🟡 High Priority (Phase 2 시작 전 해결)

| 지적사항 | 출처 | 타당성 | 판단 근거 |
|---------|------|:-----:|----------|
| **FastAPI Lifespan 미구현** | 종합평가 | ✅ **타당** | startup/shutdown 훅 없음 → Adapter 초기화 불가 |
| **Settings 미구현** | 종합평가 | ✅ **타당** | pydantic-settings + YAML 문서만 존재 |
| **Stop Hook 성능 이슈** | 문서평가, 최적화 | ✅ **타당** | 응답마다 136 tests 실행 → 느린 피드백 |
| **README와 실제 불일치** | 종합평가 | ✅ **타당** | "빠른 시작" 섹션이 완성된 것처럼 보이나 Phase 1.5 수준 |
| **Port 커버리지 낮음 (70-75%)** | 품질평가 | ✅ **타당** | Adapter 테스트에서 Port 메서드 검증 부족 |
| **Skills 미사용** | 최적화 | ✅ **타당** | Auto-invoked 컨텍스트 로딩 기회 상실 |
| **Integration 테스트 부족** | 품질평가 | ✅ **타당** | ADK, DynamicToolset, A2A 통합 테스트 없음 (Phase 2 계획) |
| **Middleware 순서 테스트 부재** | 종합평가 | ✅ **타당** | LIFO 동작 회귀 테스트 필요 |

**타당성 평가:**
- ✅ **모두 타당**: 품질 향상 및 개발 효율성에 직접 기여
- ✅ **우선순위 적절**: Phase 2 시작 전 기반 다지기

---

### 🟢 Medium Priority (Phase 2 진행 중 개선)

| 지적사항 | 출처 | 타당성 | 판단 근거 |
|---------|------|:-----:|----------|
| **ADK Sync Blocking 위험** | 종합평가 | ⚠️ **부분 타당** | Phase 2에서 주의 필요 (MCPToolset, LiteLLM 동기 메서드) |
| **AI-TDD 패턴 미반영** | 품질평가 | ✅ **타당** | 2026 베스트 프랙티스: AI 엣지 케이스 발견, 테스트 스캐폴딩 |
| **Vertical Testing 전략 누락** | 품질평가 | ✅ **타당** | 헥사고날 아키텍처 Use Case 기반 테스트 전략 미명시 |
| **브랜치 네이밍 불일치** | 종합평가 | ✅ **타당** | `feature/phase-0-setup`에 Phase 1.5까지 완료 → 혼란 |
| **A2A 통합 범위 모호** | 종합평가 | ✅ **타당** | "A2A Basic" 정의 불명확 |
| **엣지 케이스 테스트 부족** | 품질평가 | ✅ **타당** | 동시성, 경계값 테스트 부족 |
| **Phase 1.5 DoD 미갱신** | 종합평가 | ✅ **타당** | roadmap.md 체크박스 [ ] 상태 |

**타당성 평가:**
- ✅ **대부분 타당**: 장기 품질 및 명확성에 기여
- ✅ **우선순위 적절**: 긴급하지 않으나 개선 필요

---

## 💡 제시된 대안 평가

### 1. folder-readme-guide.md 처리 방안

**사용자 의견:**
> "상세 계획 수립시 별도로 계획에서 readme 작성을 포함시키는것은 어떻다고 평가하는가? 즉, claudeme에 해당 섹션을 제거하는 것에 대해 질문하고있는거다."

**평가:**
- ✅ **매우 적절**: Phase별 계획에 README 작성 포함 → 실질적, 유지보수 용이
- ✅ **CLAUDE.md 간결화**: 참조 파일 제거로 복잡도 감소
- ✅ **일관성**: roadmap.md의 "Folder Documentation" 섹션과 정보 중복 제거

**권장 조치:**
1. CLAUDE.md L158 참조 제거
2. 각 Phase 플랜에 "생성/업데이트할 README 목록" 섹션 추가
3. roadmap.md의 Folder Documentation 섹션 유지

**최종 권고:** CLAUDE.md 참조 제거, Phase 플랜에 README 작성 명시

---

### 2. PreToolUse Hook 제거 → Git pre-commit hook으로 대체

**사용자 결정:** Git pre-commit hook (커밋 시 차단) 선택

**평가:**
- ✅ **매우 적절**: Git native 기능 활용, 근본적 해결
- ✅ **2026 베스트 프랙티스 준수**: Write-time blocking 제거
- ✅ **실행 가능**: 즉시 적용 가능

**최종 권고:** PreToolUse Hook 제거 + Git pre-commit hook 추가 + SessionEnd 경고 병행

---

### 2. Stop Hook 최적화 (pytest 제거)

**제안 (문서평가, 최적화):**
```json
"Stop": [{
  "command": "ruff check src/ tests/ --fix --quiet; ruff format src/ tests/ --quiet; exit 0"
}]
```

**평가:**
- ✅ **매우 적절**: pytest는 UserPromptSubmit (commit 시)로 이동
- ✅ **효율성**: Stop에서는 빠른 포맷팅만
- ✅ **실행 가능**: 즉시 적용 가능

**추가 권고:**
```json
"UserPromptSubmit": [{
  "matcher": "commit|pr|push",
  "hooks": [{
    "command": "pytest tests/ --cov=src --cov-fail-under=80 -q || (echo '❌ Coverage below 80%' && exit 1)"
  }]
}]
```

**최종 권고:** 제안 그대로 채택

---

### 3. Skills 추가 (hexagonal-patterns, security-checklist, mcp-adk-standards)

**제안 (최적화 리포트):**
- `.claude/skills/hexagonal-patterns.md`
- `.claude/skills/security-checklist.md`
- `.claude/skills/mcp-adk-standards.md`

**평가:**
- ✅ **매우 적절**: Auto-invoked 컨텍스트 로딩으로 효율성 증대
- ✅ **구조 명확**: 각 Skill의 구조와 내용 상세히 제시
- ✅ **실행 가능**: 즉시 생성 가능

**우선순위:**
1. 🔴 `hexagonal-patterns.md` (Phase 2 시작 전 필수)
2. 🔴 `security-checklist.md` (Phase 2 시작 전 필수)
3. 🟡 `mcp-adk-standards.md` (Phase 2 진행 중)

**최종 권고:** 제안 그대로 채택, 우선순위별 순차 생성

---

### 4. Phase 2.0+ 플랜 문서 작성

**사용자 피드백:**
> "플랜은 이미 docs\plans\phase2.0.md에 작성되었고, 검토중이다. 새로운 작성 불필요하며, 단계마다 내가 직접 작성할 예정."

**평가:**
- ✅ **phase2.0.md 이미 존재**: 새로운 작성 불필요
- ✅ **사용자 주도**: 향후 Phase 플랜은 사용자가 직접 작성
- ✅ **현재 계획의 역할**: 향후 플랜 작성 시 참고 가능한 구조/템플릿 제시

**최종 권고:** Phase 플랜 작성 작업 제외, 대신 Phase 플랜 템플릿 제공

---

### 5. README Development Status 섹션 추가

**제안 (종합평가):**
```markdown
## 🚧 Development Status

**Current Phase:** Phase 1.5 (Security Layer) ✅ Complete

| Feature | Status |
|---------|:------:|
| Domain Core | ✅ Complete (91% coverage) |
| Security Layer | ✅ Complete |
| MCP Integration | 🚧 In Progress (Phase 2.0) |
| Chrome Extension | 📋 Planned (Phase 2.5) |
| A2A Integration | 📋 Planned (Phase 3) |
```

**평가:**
- ✅ **매우 적절**: 사용자 혼란 방지, 명확한 진행 상황 표시
- ✅ **실행 가능**: 즉시 추가 가능
- ✅ **유지보수 용이**: Phase 진행에 따라 업데이트 간단

**최종 권고:** 제안 그대로 채택

---

### 6. AI-TDD 워크플로우 문서화

**제안 (품질평가):**
tdd-agent.md에 AI 협업 TDD 워크플로우 추가:
- Phase 1: 테스트 요구사항 정의 (AI 엣지 케이스 제안)
- Phase 2: 테스트 작성 (Human seed, AI 생성)
- Phase 3: 구현 (AI 생성, Human 리뷰)

**평가:**
- ✅ **적절**: 2026 베스트 프랙티스 반영
- ✅ **실용적**: 현재 TDD 워크플로우와 호환
- ⚠️ **검증 필요**: Phase 2에서 실제 적용 후 효과 확인

**최종 권고:** 채택, Phase 2에서 실제 적용하며 개선

---

### 7. Port 커버리지 개선

**제안 (품질평가):**
Integration 테스트에서 모든 Port 메서드 검증
```python
async def test_implements_all_port_methods(self):
    adapter = AdkOrchestratorAdapter(...)
    assert hasattr(adapter, 'process_message')
    # 실제 동작 검증
```

**평가:**
- ✅ **적절**: Port 인터페이스 계약 준수 보장
- ✅ **실행 가능**: 테스트 작성 명확
- ⚠️ **우선순위**: Phase 2에서 Integration 테스트 추가 시 포함

**최종 권고:** 채택, Phase 2 Integration 테스트 계획에 포함

---

## 🔄 추가 대안 제시

### 1. 문서 일관성 자동 검증 Hook

**문제:** CLAUDE.md 파일 참조 오류, roadmap 불일치

**제안:**
```json
"PreToolUse": [{
  "matcher": "Edit.*CLAUDE\\.md|Edit.*roadmap\\.md",
  "hooks": [{
    "type": "command",
    "command": "python scripts/validate_doc_references.py || echo '⚠️  Document reference validation failed'"
  }]
}]
```

```python
# scripts/validate_doc_references.py
import re
from pathlib import Path

def validate_claude_md():
    """CLAUDE.md 파일 참조 검증"""
    claude_md = Path("CLAUDE.md").read_text()
    references = re.findall(r'@([^\s]+)', claude_md)

    for ref in references:
        if not Path(ref).exists():
            print(f"❌ Missing: {ref}")
            return False
    return True

if __name__ == "__main__":
    exit(0 if validate_claude_md() else 1)
```

**평가:**
- ✅ **효과적**: 문서 참조 오류 사전 방지
- ✅ **자동화**: 수동 확인 불필요
- ⚠️ **복잡도**: 스크립트 유지보수 필요

**최종 권고:** 선택적 적용 (Phase 2 이후)

---

### 2. Phase 플랜 템플릿 생성

**문제:** Phase 2.0+ 플랜 문서 누락, 향후 일관성 유지 어려움

**제안:**
```markdown
# docs/plans/phase-template.md

# Phase X.X: [Phase 제목]

**목표:** [간단한 목표 설명]

---

## 구현 전략

### X.1 [구현 항목 1]
- **대상:** ...
- **기술 스택:** ...
- **구현 포인트:** ...

### X.2 [구현 항목 2]
...

---

## 테스트 전략

| 테스트 유형 | 대상 | 커버리지 목표 |
|-----------|------|--------------|
| Unit | ... | 80% |
| Integration | ... | 70% |

---

## DoD (Definition of Done)

- [ ] 항목 1
- [ ] 항목 2
- [ ] 테스트 커버리지 목표 달성
- [ ] 문서 업데이트 완료

---

## 리스크 및 주의사항

- **리스크 1:** ...
- **완화책:** ...
```

**평가:**
- ✅ **효과적**: 향후 Phase 문서 일관성 보장
- ✅ **재사용성**: phase1.0.md, 1.5.md 구조 기반
- ✅ **실행 가능**: 즉시 생성 가능

**최종 권고:** 채택

---

### 3. ADR 자동화 강화

**문제:** adr-specialist 에이전트 존재하나 활용도 불명확

**제안:**
- 아키텍처 결정 시 ADR 자동 생성 워크플로우 명시
- CLAUDE.md에 ADR 생성 트리거 추가

```markdown
# CLAUDE.md 추가

## 🧩 Architecture Decision Records (ADR)

**자동 생성 트리거:**
- 기술 스택 선택 (예: SQLite vs PostgreSQL)
- 아키텍처 패턴 변경 (예: MCP Transport 방식)
- 보안 정책 결정 (예: Token Handshake 방식)

**프로세스:**
1. 아키텍처 결정 발생
2. adr-specialist 에이전트 호출
3. `docs/decisions/NNNN-title.md` 생성
4. 결정 컨텍스트, 선택지, 결과 문서화
```

**평가:**
- ✅ **효과적**: 아키텍처 결정 추적성 향상
- ✅ **자동화**: 에이전트 활용도 증대
- ⚠️ **시기**: Phase 2 이후 복잡도 증가 시 효과 극대화

**최종 권고:** CLAUDE.md에 지침 추가, Phase 2+ 적극 활용

---

## 📋 종합 개선 계획

### 사용자 결정사항 반영

1. ✅ **folder-readme-guide.md**: CLAUDE.md 참조 제거, Phase 플랜에 README 작성 명시
2. ✅ **main 브랜치 보호**: Git pre-commit hook 추가
3. ✅ **Phase 플랜**: phase2.0.md 이미 존재, 향후 사용자가 직접 작성
4. ✅ **문서 참조 검증**: PostToolUse Hook 추가 (CLAUDE.md, README.md, roadmap.md)
5. ✅ **comprehensive-evaluation 반영**: CORS 버그, DI Container 등 추가

### Phase 구성

```
Phase A: Critical 이슈 해결 (Claude 실행)
 ├─ A.1 CORS Middleware 순서 수정 + 관련 문서 동기화
 ├─ A.2 DI Container/Settings 스캐폴딩
 ├─ A.3 FastAPI Lifespan 구현 + implementation-guide 동기화
 ├─ A.4 Middleware 순서 테스트
 └─ A.5 문서 정리 (CLAUDE.md, README.md, roadmap.md)

Phase B: Hooks 재구성 + 문서 동기화 (Claude 실행)
 ├─ B.1 .claude/settings.json Hooks 재구성
 ├─ B.2 Git pre-commit hook 추가
 ├─ B.3 문서 참조 검증 스크립트 + Hook 추가
 ├─ B.4 Hooks 변경에 따른 문서 동기화
 │   ├─ CLAUDE.md "Development Workflow" 섹션
 │   ├─ README.md "개발 워크플로우" 섹션
 │   └─ roadmap.md Section 7 Hooks config
 └─ B.5 Phase 플랜 템플릿 생성

Phase M: 사용자 수동 작업 (Skills/Agents 개선)
 ├─ M.1 Skills 생성 (hexagonal-patterns, security-checklist, mcp-adk-standards)
 ├─ M.2 Agents 업데이트 (tdd-agent, hexagonal-architect)
 └─ M.3 선택적 Agent/Skill 추가 (phase-orchestrator, git-workflow)

Phase C: 테스트 및 품질 개선 (Phase 2 진행 중)
 └─ Phase 2와 병행
```

> **⚠️ 수행 주체 구분:**
> - **Phase A, B**: Claude가 실행 (코드 수정, 문서 업데이트, Hook/스크립트 생성)
> - **Phase M**: 사용자가 수동 실행 (Skills/Agents 파일 생성/수정)
> - **Phase C**: Phase 2 구현과 병행

---

### Phase A: Critical 이슈 해결 (즉시 실행)

**목표:** 프로젝트 진행 차단 요소 제거 (Phase 2 진입 전 필수)

> **⚠️ TDD 원칙 적용:**
> 코드 구현 시 **Red-Green-Refactor** 사이클을 엄수합니다.
> 1. **Red**: 실패하는 테스트 먼저 작성
> 2. **Green**: 테스트를 통과하는 최소 구현
> 3. **Refactor**: 코드 품질 개선 (테스트 그린 유지)
>
> **테스트 구조 준수:**
> - Unit 테스트: `tests/unit/` (Domain Layer, Fake Adapter)
> - Integration 테스트: `tests/integration/adapters/` (Adapter + 외부 시스템)
> - Import 패턴: `from src.domain.entities.tool import Tool` (절대 경로)
> - Async 테스트: `@pytest.mark.asyncio` 데코레이터
> - 네이밍: 파일 `test_<component>.py`, 클래스 `Test<Component>`, 메서드 `test_<scenario>`

#### A.1 코드 버그 수정 (P0)

| 순서 | 작업 | TDD 단계 | 산출물 | 우선순위 |
|:---:|------|:--------:|--------|:-------:|
| 1 | **Middleware 순서 회귀 테스트** | 🔴 Red | [tests/integration/adapters/test_middleware_order.py](tests/integration/adapters/test_middleware_order.py) | 🔴 P0 |
| 2 | **CORS Middleware 순서 수정** | 🟢 Green | [src/adapters/inbound/http/app.py](src/adapters/inbound/http/app.py) | 🔴 P0 |
| 3 | **DI Container 테스트** | 🔴 Red | [tests/unit/config/test_container.py](tests/unit/config/test_container.py) | 🔴 P0 |
| 4 | **DI Container 스캐폴딩** | 🟢 Green | [src/config/container.py](src/config/container.py), [src/config/settings.py](src/config/settings.py) | 🔴 P0 |
| 5 | **Lifespan 테스트** | 🔴 Red | [tests/integration/adapters/test_http_app.py](tests/integration/adapters/test_http_app.py) (기존 파일에 추가) | 🔴 P0 |
| 6 | **FastAPI Lifespan 구현** | 🟢 Green | [src/main.py](src/main.py) | 🔴 P0 |

**상세 계획:**

**A.1.1 Middleware 순서 테스트 작성 (🔴 Red First)**

```python
# tests/integration/adapters/test_middleware_order.py
# (기존 tests/integration/adapters/ 구조를 따름)
import pytest
from fastapi.testclient import TestClient

from src.adapters.inbound.http.app import create_app


class TestMiddlewareOrder:
    """Middleware LIFO 순서 회귀 테스트"""

    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    def test_cors_headers_on_403_response(self, client):
        """토큰 없이 /api/* 호출 시 403 + CORS 헤더 포함 확인"""
        response = client.post(
            "/api/chat/stream",
            json={"message": "test"},
            headers={"Origin": "chrome-extension://testextensionid"}
        )

        assert response.status_code == 403
        # CORS 헤더가 403 응답에도 포함되어야 함
        assert "access-control-allow-origin" in response.headers

    def test_options_preflight_passes(self, client):
        """CORS preflight (OPTIONS) 정상 동작 확인"""
        response = client.options(
            "/api/chat/stream",
            headers={"Origin": "chrome-extension://testextensionid"}
        )

        assert response.status_code == 200
        assert "access-control-allow-methods" in response.headers

    def test_non_extension_origin_rejected(self, client):
        """chrome-extension:// 이외 Origin은 CORS 거부"""
        response = client.options(
            "/api/chat/stream",
            headers={"Origin": "http://malicious-site.com"}
        )

        # CORS 미들웨어가 허용하지 않는 Origin
        assert "access-control-allow-origin" not in response.headers
```

**A.1.2 CORS Middleware 순서 수정 (🟢 Green)**

현재 코드 (잘못된 순서):
```python
# src/adapters/inbound/http/app.py
app.add_middleware(CORSMiddleware, ...)      # 먼저 추가
app.add_middleware(ExtensionAuthMiddleware)   # 나중 추가 → LIFO로 먼저 실행
```

수정:
```python
# Middleware 순서 (중요):
# FastAPI는 LIFO(Last-In-First-Out) 방식으로 미들웨어를 실행합니다.
# 1. ExtensionAuthMiddleware 먼저 추가 → innermost (나중에 실행)
# 2. CORSMiddleware 나중 추가 → outermost (먼저 실행)
# 이유: CORS preflight (OPTIONS) 요청과 403 에러 응답에 CORS 헤더가 포함되어야 합니다.
app.add_middleware(ExtensionAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-Extension-Token", "Content-Type"],
    allow_credentials=False,
)
```

**A.1.3 DI Container 테스트 작성 (🔴 Red First)**

```python
# tests/unit/config/test_container.py
import pytest
from src.config.settings import Settings
from src.config.container import Container


class TestSettings:
    """Settings 기본값 검증"""

    def test_default_server_host(self):
        settings = Settings()
        assert settings.server_host == "localhost"

    def test_default_server_port(self):
        settings = Settings()
        assert settings.server_port == 8000


class TestContainer:
    """DI Container 스캐폴딩 검증"""

    def test_container_provides_settings(self):
        container = Container()
        settings = container.settings()
        assert isinstance(settings, Settings)

    def test_settings_singleton(self):
        container = Container()
        settings1 = container.settings()
        settings2 = container.settings()
        assert settings1 is settings2
```

**A.1.4 DI Container 스캐폴딩 (🟢 Green)**

```python
# src/config/container.py
from dependency_injector import containers, providers
from src.config.settings import Settings

class Container(containers.DeclarativeContainer):
    """DI Container - Phase 2에서 Adapters 추가 예정"""

    config = providers.Configuration()
    settings = providers.Singleton(Settings)

    # Phase 2에서 추가 예정:
    # - orchestrator_adapter
    # - dynamic_toolset
    # - storage adapters
```

```python
# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application Settings"""

    server_host: str = "localhost"
    server_port: int = 8000

    # Phase 2에서 추가 예정:
    # - llm_default_model
    # - storage_data_dir
    # - health_check_interval

    class Config:
        env_file = ".env"
```

**A.1.5 Lifespan 테스트 작성 (🔴 Red First)**

```python
# tests/integration/adapters/test_http_app.py 에 추가
# (기존 TestCorsConfiguration, TestSecurityMiddleware 클래스와 동일 파일)

class TestLifespan:
    """FastAPI Lifespan 동작 검증"""

    def test_app_starts_with_lifespan(self):
        """lifespan이 설정된 앱이 정상 생성됨"""
        from src.adapters.inbound.http.app import create_app
        app = create_app()
        assert app.router.lifespan_context is not None

    def test_health_endpoint_after_startup(self):
        """startup 후 /health 정상 응답"""
        from src.adapters.inbound.http.app import create_app
        client = TestClient(create_app())
        response = client.get("/health")
        assert response.status_code == 200
```

**A.1.6 FastAPI Lifespan 구현 (🟢 Green)**

```python
# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.adapters.inbound.http.app import create_app

app = create_app()
```

```python
# src/adapters/inbound/http/app.py 에 lifespan 추가
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    # Phase 2에서 추가: Adapter 초기화
    # await orchestrator.initialize()
    # await health_monitor.start()
    yield
    # Shutdown
    # Phase 2에서 추가: 리소스 정리
    # await orchestrator.close()
    # await health_monitor.stop()

def create_app():
    app = FastAPI(
        title="AgentHub API",
        lifespan=lifespan,
    )
    # ... middleware, routes
    return app
```

---

#### A.2 코드 변경에 따른 문서 동기화 (P0)

CORS Middleware 순서 수정 + DI Container + Lifespan에 따른 **연쇄 문서 업데이트**:

| 작업 | 대상 파일 | 변경 내용 | 우선순위 |
|------|----------|----------|:-------:|
| **implementation-guide.md Section 9.3 수정** | [docs/implementation-guide.md](docs/implementation-guide.md) | CORS 코드 예시: (1) 미들웨어 순서 수정 (2) `allow_origins` → `allow_origin_regex` (3) LIFO 주석 추가 | 🔴 P0 |
| **implementation-guide.md Section 3 수정** | [docs/implementation-guide.md](docs/implementation-guide.md) | `@app.on_event("startup")` → `lifespan` 패턴 | 🔴 P0 |
| **architecture.md Config Layer 상세화** | [docs/architecture.md](docs/architecture.md) | Section 3 Config Layer (L148-154): DI Container 실제 구현 반영, `container.py`/`settings.py` 설명 추가 | 🟡 P1 |

**상세 계획:**

**A.2.1 implementation-guide.md Section 9.3 CORS 설정**

현재 (잘못된 코드):
```python
# 현재 implementation-guide.md (L1044-1070)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],  # ❌ 패턴 매칭 불가
    ...
)
app.add_middleware(ExtensionAuthMiddleware)  # ❌ LIFO로 인해 먼저 실행
```

수정:
```python
# Middleware 순서 (LIFO - 나중에 추가한 것이 먼저 실행):
# 1. ExtensionAuthMiddleware 먼저 추가 → innermost (나중 실행)
# 2. CORSMiddleware 나중 추가 → outermost (먼저 실행)
app.add_middleware(ExtensionAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-Extension-Token", "Content-Type"],
    allow_credentials=False,
)
```

**A.2.2 implementation-guide.md Section 3 Lifespan 패턴**

현재:
```python
@app.on_event("startup")  # ❌ deprecated
```

수정: A.1.3에서 구현하는 lifespan 패턴으로 코드 예시 교체

**A.2.3 architecture.md Config Layer 상세화**

현재 (L148-154):
```markdown
| **Settings** | pydantic-settings + YAML (환경변수 > YAML > 기본값) |
| **Container** | dependency-injector DI 컨테이너 |
```

추가: DI Container 실제 파일 구조 및 사용 패턴 설명
- `container.py`: `DeclarativeContainer` 기반 의존성 정의
- `settings.py`: `BaseSettings` 기반 환경설정 (환경변수 > .env > 기본값)
- Phase 2에서 Adapter providers 추가 예정

---

#### A.3 문서 정리 (P1)

| 작업 | 산출물 | 우선순위 |
|------|--------|:-------:|
| **CLAUDE.md folder-readme-guide 참조 제거** | L212 `@.claude/folder-readme-guide.md` 참조 삭제 | 🟡 P1 |
| **README.md Development Status 추가** | "주요 기능" 섹션 이전에 진행 상황 표시 | 🟡 P1 |
| **roadmap.md 업데이트** | Phase 0 체크리스트에 adr-specialist 추가, Phase 1.5 DoD 갱신 | 🟡 P1 |

**상세 계획:**

**A.3.1 README.md 수정**
```markdown
# 삽입 위치: "## 주요 기능" 섹션 이전
## 🚧 Development Status

**Current Phase:** Phase 1.5 (Security Layer) ✅ Complete

| Feature | Status | Coverage |
|---------|:------:|:--------:|
| Domain Core | ✅ Complete | 91% |
| Security Layer | ✅ Complete | - |
| MCP Integration | 🚧 Planned (Phase 2.0) | - |
| Chrome Extension | 📋 Planned (Phase 2.5) | - |
| A2A Integration | 📋 Planned (Phase 3) | - |

📖 See [docs/roadmap.md](docs/roadmap.md) for detailed timeline.
```

**A.3.2 roadmap.md 업데이트**
```markdown
# Phase 0 체크리스트에 추가:
| ✅ | `adr-specialist.md` 작성 | - |

# "7. Development Workflow" 섹션에 추가:
### 브랜치 전략
- **Trunk-Based Development** 채택 (MVP 단계)
- feature/* 브랜치에서 개발, main으로 PR
- Phase 완료 시 브랜치명 변경 (예: feature/phase-1.5-complete)
```

---

### Phase B: Hooks & Skills 최적화 (Phase 2 시작 전)

**목표:** 개발 워크플로우 효율화, 2026 베스트 프랙티스 적용

**사용자 결정사항 반영:**
- ✅ Git pre-commit hook 추가
- ✅ 문서 참조 검증 Hook 추가 (CLAUDE.md, README.md, roadmap.md)

#### B.1 Hooks 재구성

**작업:**
1. `.claude/settings.json` Hooks 수정
2. Git pre-commit hook 추가

**상세 계획:**

**B.1.1 settings.json 수정**
```json
{
  "enabledPlugins": {
    "tdd-workflows@claude-code-workflows": true,
    "full-stack-orchestration@claude-code-workflows": true
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "description": "Auto-format code after edits",
          "command": "ruff check src/ tests/ --fix --quiet 2>/dev/null; ruff format src/ tests/ --quiet 2>/dev/null"
        }]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{
          "type": "command",
          "description": "Quick unit test validation",
          "command": "pytest tests/unit/ -q --tb=line --maxfail=1 2>&1 | head -20 || echo '⚠️  Unit tests failed - review before commit'"
        }]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "commit|pr|push",
        "hooks": [{
          "type": "command",
          "description": "Full test suite with coverage",
          "command": "pytest tests/ --cov=src --cov-fail-under=80 -q || (echo '❌ Coverage below 80%' && exit 1)"
        }]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [{
          "type": "command",
          "description": "Warn if session on main branch",
          "command": "git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -qx main && echo '⚠️  Session ended on main branch - ensure commits are reviewed' || exit 0"
        }]
      }
    ]
  }
}
```

**변경 사항:**
- ❌ **제거:** PreToolUse Hook (main 브랜치 차단 → Git pre-commit hook으로 대체)
- ✅ **추가:** PostToolUse Hook (코드 작성 즉시 포맷팅)
- ✅ **추가:** UserPromptSubmit Hook (commit 전 전체 테스트)
- ✅ **추가:** SessionEnd Hook (main 브랜치 소프트 경고 - pre-commit의 보완)
- ✅ **변경:** Stop Hook (전체 테스트 → Unit 테스트만)

> **Git pre-commit hook + SessionEnd Hook 병행 이유 (사용자 결정):**
> - Git pre-commit hook: 커밋 시 **하드 블로킹** (main 브랜치 커밋 차단)
> - SessionEnd Hook: 세션 종료 시 **소프트 경고** (main 브랜치에서 작업 중임을 알림)
> - 두 가지는 서로 다른 시점에서 보호하므로 중복이 아님

**B.1.2 Git pre-commit hook 추가**
```bash
# .git/hooks/pre-commit 생성 (실행 권한 부여)
#!/bin/bash
if [ "$(git branch --show-current)" = "main" ]; then
  echo "❌ Direct commits to main branch are blocked"
  echo "   Please create a feature branch: git checkout -b feature/your-feature"
  exit 1
fi
exit 0
```

Windows:
```bash
# .git/hooks/pre-commit (Git Bash)
chmod +x .git/hooks/pre-commit
```

**B.1.3 문서 참조 검증 Hook 추가** (사용자 요청)

```python
# scripts/validate_doc_references.py
"""문서 참조 검증 - CLAUDE.md, README.md, roadmap.md"""
import re
from pathlib import Path
import sys

def validate_file_references(file_path: str, pattern: str) -> list[str]:
    """파일 내 @경로 참조 검증"""
    if not Path(file_path).exists():
        return []

    content = Path(file_path).read_text(encoding='utf-8')
    references = re.findall(pattern, content)

    missing = []
    for ref in references:
        # @docs/... 형태에서 경로 추출
        path = ref if '/' in ref else None
        if path and not Path(path).exists():
            missing.append(f"{file_path}: @{path} 파일 없음")

    return missing

def main():
    files_to_check = {
        'CLAUDE.md': r'@([^\s\)]+)',
        'README.md': r'@([^\s\)]+)',
        'docs/roadmap.md': r'@([^\s\)]+)',
    }

    all_missing = []
    for file_path, pattern in files_to_check.items():
        missing = validate_file_references(file_path, pattern)
        all_missing.extend(missing)

    if all_missing:
        print("❌ 누락된 파일 참조 발견:")
        for msg in all_missing:
            print(f"   {msg}")
        return 1

    print("✅ 모든 파일 참조 유효")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

`.claude/settings.json`에 Hook 추가:
```json
"PostToolUse": [
  {
    "matcher": "Edit.*(CLAUDE\\.md|README\\.md|roadmap\\.md)",
    "hooks": [{
      "type": "command",
      "description": "Validate document references",
      "command": "python scripts/validate_doc_references.py 2>/dev/null || echo '⚠️  Document reference check failed (non-blocking)'"
    }]
  }
]
```

---

#### B.4 Hooks 변경에 따른 문서 동기화 (P1)

Hooks 재구성(B.1)에 따라 **3개 문서의 Hooks 관련 섹션 업데이트** 필요:

| 작업 | 대상 파일 | 현재 문제 | 변경 내용 |
|------|----------|----------|----------|
| **CLAUDE.md "Development Workflow" 수정** | [CLAUDE.md](CLAUDE.md) L67-74 | PreToolUse Hook 언급, Stop Hook에 pytest 포함으로 기술 | PreToolUse → Git pre-commit hook으로 변경, Stop Hook → 포맷팅만, 새 Hook 추가 반영 |
| **README.md "개발 워크플로우" 수정** | [README.md](README.md) L139-154 | PreToolUse Hook 자동 차단 언급, Stop Hook 설명 불완전 | Git pre-commit hook 반영, PostToolUse/UserPromptSubmit/SessionEnd Hook 추가 |
| **roadmap.md Section 7 수정** | [docs/roadmap.md](docs/roadmap.md) L565-589 | 구식 Hooks config (PreToolUse, 간소화된 Stop) | 새 settings.json 전체 Hooks config 반영 |

**상세 계획:**

**B.4.1 CLAUDE.md "Development Workflow" 섹션 (L67-74)**

현재:
```markdown
**자동화 (Hooks):**
- **PreToolUse Hook**: main 브랜치 직접 Edit/Write 차단 (항상 feature 브랜치 사용)
- **Stop Hook**: 응답 완료 시 자동 실행 (ruff 린트/포맷, pytest)
```

수정:
```markdown
**자동화 (Hooks):**
- **PostToolUse Hook**: 코드 수정 후 자동 ruff 포맷팅
- **Stop Hook**: 응답 완료 시 Unit 테스트 실행
- **UserPromptSubmit Hook**: commit/pr/push 시 전체 테스트 + 커버리지 검증
- **Git pre-commit hook**: main 브랜치 직접 커밋 차단
- **GitHub Actions**: PR 시 커버리지 80% 미만 차단
```

**B.4.2 README.md "개발 워크플로우" 섹션 (L139-154)**

현재:
```markdown
**브랜치 보호:**
- main 브랜치에서 직접 수정 시도 → PreToolUse Hook이 자동 차단
```

수정:
```markdown
**브랜치 보호:**
- main 브랜치 직접 커밋 → Git pre-commit hook이 차단
- 항상 feature 브랜치에서 작업
```

Stop Hook 설명도 업데이트:
```markdown
[Claude 작업 완료] → Stop Hook 자동 실행:
  ✓ ruff check src/ tests/ --fix    # 린트 자동 수정
  ✓ ruff format src/ tests/          # 코드 포맷팅
  ✓ pytest tests/unit/ -q            # Unit 테스트 실행
```

**B.4.3 roadmap.md Section 7 Hooks config (L565-589)**

현재 (간소화된 구식 config) → B.1.1에서 정의한 새 settings.json config로 교체

---

#### B.5 Phase 플랜 템플릿 생성

**작업:** `docs/plans/phase-template.md` 생성
**수행:** Claude 실행

(Phase A "추가 대안 제시" 섹션 2에서 정의한 템플릿 그대로 적용)

---

### Phase M: 사용자 수동 작업 (Skills/Agents 개선)

> **⚠️ 이 Phase는 사용자가 직접 수행합니다. Claude는 실행하지 않습니다.**
> 아래는 사용자가 참조할 수 있도록 각 작업의 내용과 추천 구조를 기술합니다.

#### M.1 Skills 생성 (사용자 수동)

| Skill | 파일 | 우선순위 | 시기 |
|-------|------|:-------:|------|
| **hexagonal-patterns** | `.claude/skills/hexagonal-patterns.md` | 🔴 필수 | Phase 2 시작 전 |
| **security-checklist** | `.claude/skills/security-checklist.md` | 🔴 필수 | Phase 2 시작 전 |
| **mcp-adk-standards** | `.claude/skills/mcp-adk-standards.md` | 🟡 중요 | Phase 2 진행 중 |

**각 Skill 추천 구조:**

```yaml
---
name: [skill-name]
description: [Auto-invoke 트리거 문구 - 이 문구가 매칭되면 자동 로드]
tags: [관련 태그]
---

# [Skill 제목]

## 핵심 원칙
[IMPORTANT로 강조할 필수 사항]

## 코드 패턴 예시
[올바른/잘못된 예시 대비]

## 체크리스트
[작업 시 필수 확인 항목]

## 참조 문서
[@docs/... 형태로 프로젝트 내 문서 참조]
```

**hexagonal-patterns.md 주요 내용:**
- Domain Layer 순수성 원칙 (외부 import 금지)
- Port/Adapter 분리 패턴
- Dependency Injection 패턴
- Fake Adapter 테스트 패턴

**security-checklist.md 주요 내용:**
- Token Handshake 패턴
- CORS Configuration (`allow_origin_regex` 사용, LIFO 순서 주의)
- Extension Client Session Storage 사용
- 보안 체크리스트

**mcp-adk-standards.md 주요 내용:**
- ADK Import 경로 (`google.adk.*`)
- MCPToolset 비동기 패턴
- DynamicToolset BaseToolset 상속 패턴
- MCP Transport (Streamable HTTP 우선, SSE fallback)

---

#### M.2 Agents 업데이트 (사용자 수동)

| Agent | 파일 | 추가 내용 | 시기 |
|-------|------|----------|------|
| **tdd-agent** | `.claude/agents/tdd-agent.md` | AI 협업 TDD 워크플로우 (2026) | Phase 2 시작 전 |
| **hexagonal-architect** | `.claude/agents/hexagonal-architect.md` | Vertical Testing 전략 | Phase 2 시작 전 |

**tdd-agent.md 추가 내용 요약:**
- AI 협업 TDD 워크플로우 (Human seed → AI 생성 → Human 리뷰)
- 행동 기반 테스트 원칙 (구현 무관 테스트 vs 구현 세부사항 테스트)
- 엣지 케이스 제안 패턴 (동시성, 경계값, 에러 조건)
- 참고: [Test-Driven Development with AI (2026)](https://www.readysetcloud.io/blog/allen.helton/tdd-with-ai/)

**hexagonal-architect.md 추가 내용 요약:**
- Vertical Testing 전략 (수직 슬라이스 테스트)
- 테스트 피라미드 (Unit → Integration → E2E)
- In-Memory First 개발 흐름
- 참고: [Hexagonal Architecture Testing (2026)](https://medium.com/codex/a-testing-strategy-for-a-domain-centric-architecture-e-g-hexagonal-9e8d7c6d4448)

---

#### M.3 선택적 Agent/Skill 추가 (사용자 수동, 추후)

| 항목 | 유형 | 파일 | 용도 |
|------|------|------|------|
| **phase-orchestrator** | Agent | `.claude/agents/phase-orchestrator.md` | Phase DoD 검증, 완료 조건 자동 체크 |
| **git-workflow** | Skill | `.claude/skills/git-workflow.md` | 브랜치 전략, PR 템플릿, 커밋 컨벤션 |
| **ADR 자동화 지침** | CLAUDE.md 섹션 | CLAUDE.md | ADR 생성 트리거 및 프로세스 명시 |

이들은 Phase 2 이후 복잡도 증가 시 효과가 극대화됩니다.

---

### Phase C: 테스트 전략 개선 (Phase 2 진행 중)

**목표:** 테스트 커버리지 및 품질 향상

#### C.1 Port 커버리지 개선

**작업:**
- `tests/integration/adapters/test_orchestrator_adapter.py` 작성
- Port 인터페이스의 모든 메서드 실제 동작 검증

**DoD:**
- [ ] Port 커버리지 90% 이상
- [ ] 모든 Port 메서드 Integration 테스트 검증

---

#### C.2 Integration 테스트 추가

**작업:**
- ADK Orchestrator 통합 테스트
- DynamicToolset MCP 연결 테스트
- (Phase 3) A2A Client/Server 테스트

**DoD:**
- [ ] Integration 커버리지 70% 이상
- [ ] MCP 테스트 서버 연결 성공
- [ ] 실제 LLM 응답 테스트 통과

---

#### C.3 엣지 케이스 테스트 (AI 활용)

**작업:**
- AI-TDD 워크플로우 적용
- 동시성, 경계값, 에러 조건 테스트 생성

**DoD:**
- [ ] 동시성 테스트 최소 5개
- [ ] 경계값 테스트 최소 10개
- [ ] AI 제안 엣지 케이스 문서화

---

## 📊 개선 계획 타임라인

```
Phase A (Claude 실행 - 즉시):
  ├─ A.1: 코드 버그 수정 (CORS, DI Container, Lifespan)
  ├─ A.2: CORS/Lifespan 관련 문서 동기화 (implementation-guide.md)
  └─ A.3: 문서 정리 (CLAUDE.md, README.md, roadmap.md)

Phase B (Claude 실행 - Phase 2 시작 전):
  ├─ B.1-B.3: Hooks 재구성 + Git hook + 문서 참조 검증 스크립트
  ├─ B.4: Hooks 변경 문서 동기화 (CLAUDE.md, README.md, roadmap.md)
  └─ B.5: Phase 플랜 템플릿

Phase M (사용자 수동 - Phase 2 시작 전/진행 중):
  ├─ M.1: Skills 생성 (hexagonal-patterns, security-checklist)
  ├─ M.2: Agents 업데이트 (tdd-agent, hexagonal-architect)
  └─ M.3: 선택적 추가 (mcp-adk-standards, phase-orchestrator 등)

Phase C (Phase 2 진행 중):
  ├─ C.1: Port 커버리지 개선
  ├─ C.2: Integration 테스트 추가
  └─ C.3: 엣지 케이스 테스트 (AI 활용)
```

---

## ✅ DoD (Definition of Done)

### Phase A 완료 조건 (Claude 실행)

**코드 + 테스트 (TDD):**
- [ ] Middleware 순서 회귀 테스트 작성 (`tests/integration/adapters/test_middleware_order.py`) - 🔴 Red First
- [ ] CORS Middleware 순서 수정 (`src/adapters/inbound/http/app.py`) - 🟢 Green
- [ ] DI Container 테스트 작성 (`tests/unit/config/test_container.py`) - 🔴 Red First
- [ ] DI Container 스캐폴딩 (`src/config/container.py`, `src/config/settings.py`) - 🟢 Green
- [ ] Lifespan 테스트 작성 (`tests/integration/adapters/test_http_app.py` 확장) - 🔴 Red First
- [ ] FastAPI Lifespan 구현 (`src/adapters/inbound/http/app.py`) - 🟢 Green
- [ ] 전체 테스트 통과 확인 (`pytest` - 커버리지 80% 이상 유지)

**문서 동기화:**
- [ ] `docs/implementation-guide.md` Section 9.3 CORS 코드 동기화
- [ ] `docs/implementation-guide.md` Section 3 Lifespan 패턴 동기화
- [ ] `docs/architecture.md` Config Layer 상세화
- [ ] CLAUDE.md L212 folder-readme-guide.md 참조 제거
- [ ] README.md Development Status 섹션 추가
- [ ] roadmap.md 업데이트 (adr-specialist, Phase 1.5 DoD 갱신)

### Phase B 완료 조건 (Claude 실행)
- [ ] `.claude/settings.json` Hooks 재구성 (PreToolUse 제거, PostToolUse/UserPromptSubmit/SessionEnd 추가)
- [ ] `.git/hooks/pre-commit` 생성 및 테스트
- [ ] `scripts/validate_doc_references.py` 생성 + PostToolUse Hook 등록
- [ ] `scripts/validate_doc_references.py` 실행 성공 (Phase A 문서 정리 후 참조 유효성 확인)
- [ ] CLAUDE.md "Development Workflow" 섹션 동기화 (Hooks 변경 반영)
- [ ] README.md "개발 워크플로우" 섹션 동기화 (Hooks 변경 반영)
- [ ] roadmap.md Section 7 Hooks config 동기화
- [ ] `docs/plans/phase-template.md` 생성

### Phase M 완료 조건 (사용자 수동)
- [ ] `.claude/skills/hexagonal-patterns.md` 생성
- [ ] `.claude/skills/security-checklist.md` 생성
- [ ] `tdd-agent.md` AI-TDD 워크플로우 추가
- [ ] `hexagonal-architect.md` Vertical Testing 전략 추가
- [ ] (선택) `.claude/skills/mcp-adk-standards.md` 생성 (Phase 2 진행 중)

### Phase C 완료 조건 (Phase 2 진행 중)
- [ ] Port 커버리지 90% 이상
- [ ] Integration 커버리지 70% 이상
- [ ] 엣지 케이스 테스트 20개 이상

---

## 🎯 예상 효과

### 개발 효율성
- ✅ **Hooks 최적화**: 피드백 속도 50% 향상 (Stop Hook pytest 제거)
- ✅ **Skills 활용**: 컨텍스트 로딩 자동화, 수동 에이전트 호출 감소
- ✅ **문서 일관성**: Phase 플랜 템플릿으로 향후 작성 시간 단축

### 코드 품질
- ✅ **AI-TDD**: 엣지 케이스 발견률 증가
- ✅ **Port 커버리지**: 인터페이스 계약 준수 보장
- ✅ **Integration 테스트**: 실제 연결 안정성 향상

### 프로젝트 일관성
- ✅ **문서 동기화**: README, roadmap, Phase 플랜 일치
- ✅ **브랜치 전략 명확화**: 혼란 제거
- ✅ **ADK 버전 확정**: 리스크 제거

---

## 📚 참고 자료

### 리포트 출처
- `docs/reports/AgentHub 품질 평가 보고서.md`
- `docs/reports/AgentHub 프로젝트 문서 종합 평가 보고서.md`
- `docs/reports/AgentHub 프로젝트 종합 평가.md`
- `docs/reports/claude-code-optimization.md`
- `docs/reports/comprehensive-evaluation-2026-01-29.md`

### 외부 참조
- [Test-Driven Development with AI (2026)](https://www.readysetcloud.io/blog/allen.helton/tdd-with-ai/)
- [Hexagonal Architecture Testing (2026)](https://medium.com/codex/a-testing-strategy-for-a-domain-centric-architecture-e-g-hexagonal-9e8d7c6d4448)
- [Claude Code Hooks Best Practices (2026)](https://www.eesel.ai/blog/hooks-in-claude-code)
- [Forcing Claude Code to TDD (2026)](https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/)

---

*계획 수립일: 2026-01-29*
*예상 완료일: Phase A (2일), Phase B (3일), Phase C (Phase 2와 병행)*
