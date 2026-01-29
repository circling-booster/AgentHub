# AgentHub 종합 평가 보고서

**평가일:** 2026-01-29
**대상:** Phase 1.5 완료 시점 (feature/phase-0-setup 브랜치)
**교차검증:** 웹 검색 기반 최신 스펙 확인 완료
**평가자:** Claude Code (Sonnet 4.5)

---

## 목차

1. [프로젝트 현황 요약](#1-프로젝트-현황-요약)
2. [감사 보고서 지적사항별 평가](#2-감사-보고서-지적사항별-평가)
3. [로드맵 분석: 누락/모호/모순](#3-로드맵-분석-누락모호모순)
4. [프로젝트 방향성 평가 및 조언](#4-프로젝트-방향성-평가-및-조언)
5. [감사 보고서 종합 재평가](#5-감사-보고서-종합-재평가)
6. [최종 권고사항](#6-최종-권고사항)
7. [참조 자료](#7-참조-자료)

---

## 1. 프로젝트 현황 요약

### 1.1 완료된 Phase

| Phase | 상태 | 핵심 산출물 |
|-------|:----:|------------|
| **Phase 0** | ✅ 완료 | 서브에이전트 4종, Hooks, CI/CD, 테스트 인프라 |
| **Phase 1** | ✅ 완료 | Domain Layer (엔티티 7종, 서비스 4종, 포트 6종), 173 tests, 커버리지 90.84% |
| **Phase 1.5** | ✅ 완료 | Token Handshake, CORS, Auth Middleware, SQLite WAL |

### 1.2 미착수 Phase

| Phase | 상태 | 핵심 목표 |
|-------|:----:|----------|
| **Phase 2** | ❌ 미착수 | ADK/MCP 통합, DynamicToolset, Chat API |
| **Phase 2.5** | ❌ 미착수 | Chrome Extension (WXT), Offscreen Document |
| **Phase 3** | ❌ 미착수 | A2A 기본 통합, E2E 테스트 |

### 1.3 정량 지표

- **테스트**: 173개 통과 (unit 130+, integration 20+)
- **커버리지**: 90.84% (목표 80% 초과 달성)
- **Domain 순수성**: 외부 import 0건 (완벽)
- **코드 품질**: ruff + mypy 설정 완료, CI 자동화
- **브랜치**: feature/phase-0-setup (clean)
- **최근 커밋**: d8399f8 (ruff 린트 수정), bd1370a (Phase 1.5 완료)

### 1.4 구현 현황 상세

#### ✅ 구현 완료

**Domain Layer** (`src/domain/`):
- Entities: Agent, Endpoint, Conversation, Message, Tool, ToolCall, Enums
- Services: OrchestratorService, RegistryService, ConversationService, HealthMonitorService
- Ports: ChatPort, ManagementPort (inbound), OrchestratorPort, ToolsetPort, StoragePort, A2aPort (outbound)
- Exceptions: 10+ 도메인 예외 (DomainException 기반)

**Adapters Layer** (`src/adapters/`):
- Inbound HTTP: FastAPI app factory, CORS, Auth middleware, /auth/token, /health 엔드포인트
- Outbound Storage: SQLite WAL 기반 ConversationStorage (asyncio.Lock + 싱글톤 연결)
- Security: TokenProvider, ExtensionAuthMiddleware, Origin 검증

**Test Infrastructure** (`tests/`):
- Unit tests: 130+ (엔티티, 서비스, 도메인 로직)
- Integration tests: 20+ (SQLite, HTTP routes, Security)
- Fake Adapters: OrchestratorPort, ToolsetPort, StoragePort 구현체
- pytest + pytest-asyncio + pytest-cov 설정 완료

**Claude Code Integration** (`.claude/`):
- Subagents: tdd-agent, code-reviewer, security-reviewer, hexagonal-architect
- Hooks: Stop (ruff lint/format + pytest), PreToolUse (main 브랜치 보호)
- Settings: TDD workflows, full-stack orchestration 플러그인 활성화

#### ❌ 미구현 (Phase 2+ 범위)

- ADK Orchestrator Adapter (DynamicToolset, LlmAgent 연동)
- MCP Toolset 구현 (MCPToolset, Streamable HTTP/SSE)
- Chat API (POST /api/chat/stream, SSE 스트리밍)
- MCP Management API (서버 등록/조회/삭제)
- Chrome Extension (WXT, Offscreen Document, Token handshake client)
- DI Container 구현 (dependency-injector 설정)
- FastAPI Lifespan (startup/shutdown 훅)
- A2A 통합 (Agent Card, JSON-RPC client)
- E2E 테스트 시나리오

---

## 2. 감사 보고서 지적사항별 평가

### 2.1 CORS Preflight Rejection (Middleware Ordering)

**감사 판정:** Fail — "AuthMiddleware가 CORSMiddleware보다 먼저 실행되어 OPTIONS 요청 차단"

**실제 평가: 부분적으로 타당 — 코드에 실제 버그 존재**

#### 현재 구현 분석

[src/adapters/inbound/http/app.py#L31-L40](src/adapters/inbound/http/app.py#L31-L40):
```python
app.add_middleware(CORSMiddleware, ...)      # 먼저 추가
app.add_middleware(ExtensionAuthMiddleware)   # 나중 추가
```

코드 주석은 "CORSMiddleware 먼저 추가 → outermost"라고 기술하지만, **Starlette/FastAPI의 `add_middleware`는 LIFO(Last-In-First-Out)** 방식으로 동작합니다.

#### 웹 검증 결과

[FastAPI Discussion #10366](https://github.com/fastapi/fastapi/discussions/10366):
> "in the starlette code, we see that `add_middleware` adds a middleware to the beginning of list for some reason, which is very unobvious and leads to errors with middlewares that depend on the order"

[Starlette Issue #479](https://github.com/Kludex/starlette/issues/479):
> "the order is inverse on the order you declare them"

[Medium - CORS Dilemma](https://medium.com/@saurabhbatham17/navigating-middleware-ordering-in-fastapi-a-cors-dilemma-8be88ab2ee7b):
> "When using `CORSMiddleware` alongside `AuthenticationMiddleware`, this behavior leads to CORS errors on improper authorization because `AuthenticationMiddleware` is executed first"

#### 실제 동작 분석

현재 순서에서:
- **마지막에 추가된 `ExtensionAuthMiddleware`가 실제로 outermost** (먼저 실행)
- **OPTIONS 요청**: [security.py:81](src/adapters/inbound/http/security.py#L81)에서 `if method == "OPTIONS": return await call_next(request)`로 통과시키므로 **preflight 자체는 정상 동작**
- **Auth 실패 응답 (403)**: ExtensionAuthMiddleware가 직접 `JSONResponse(403)`를 반환하면 CORSMiddleware를 거치지 않아 **CORS 헤더가 누락됨** → 브라우저에서 CORS 에러로 표시

#### 버그 분류

| 이슈 | 상태 | 심각도 |
|------|:----:|:------:|
| OPTIONS 차단 문제 | ✅ 해당 없음 | - |
| 403 응답 CORS 헤더 누락 | ❌ **실제 버그** | 🟡 중간 |
| 주석과 실제 동작 불일치 | ❌ **문서 버그** | 🟢 낮음 |

#### 개선 방법

**방법 1: 미들웨어 순서 반전 (권장)**
```python
app.add_middleware(ExtensionAuthMiddleware)   # 먼저 추가
app.add_middleware(CORSMiddleware, ...)       # 나중 추가 (outermost)
```

**방법 2: Starlette 래핑 패턴**
```python
app = CORSMiddleware(app, ...)  # 명시적 래핑
```

**구현 난이도:** 낮음 (10분 이내 수정 가능)

**참조:**
- [FastAPI CORS 공식 문서](https://fastapi.tiangolo.com/tutorial/cors/)
- [Starlette Middleware 문서](https://www.starlette.io/middleware/)
- [Medium - Navigating Middleware Ordering](https://medium.com/@saurabhbatham17/navigating-middleware-ordering-in-fastapi-a-cors-dilemma-8be88ab2ee7b)

---

### 2.2 Sync Blocking in Async Factory (Event Loop Blocking)

**감사 판정:** Fail — "ADK/LiteLLM의 동기 메서드가 이벤트 루프 차단"

**실제 평가: 타당하지만 현재 단계에서는 해당 없음**

#### 현재 상태

- ADK Orchestrator Adapter는 **아직 구현되지 않음** (Phase 2 영역)
- [docs/implementation-guide.md#2-dynamictoolset-구현](docs/implementation-guide.md#2-dynamictoolset-구현)에 `asyncio.to_thread` 패턴이 이미 문서화되어 있음
- [docs/risk-assessment.md#21-비동기-블로킹-병목](docs/risk-assessment.md#21-비동기-블로킹-병목)에도 완화책 기술됨

#### 웹 검증: ADK 실제 이슈 확인

**Issue #755 - Event Loop Conflicts:**
```
asyncio.run() cannot be called from a running event loop
```
[GitHub Issue #755](https://github.com/google/adk-python/issues/755)

**Issue #3788 - Blocking Behavior:**
> "When using `MCPToolset` with `StreamableHTTPConnectionParams`, `httpx.RemoteProtocolError` causes blocking behavior where the Agent continues waiting for a response that will never come"
[GitHub Issue #3788](https://github.com/google/adk-python/issues/3788)

**Issue #3237 - Latency:**
> "Tracing reveals that `McpToolset.get_tools()` is invoked multiple times during a single streamed interaction, repeatedly reconstructing the same tool list"
[GitHub Issue #3237](https://github.com/google/adk-python/issues/3237)

**Issue #1267 - Intermittent Errors:**
> "The call to `await toolset.get_tools()` intermittently fails with a 400 Bad Request from the MCP server, causing an `anyio.BrokenResourceError`"
[GitHub Issue #1267](https://github.com/google/adk-python/issues/1267)

#### ADK 공식 권장 패턴

[ADK Tool Performance Guide](https://google.github.io/adk-docs/tools-custom/performance/):
```python
async def cpu_intensive_tool(data: list) -> dict:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, expensive_computation, data)
    return {"result": result}
```

#### 결론

| 현재 단계 | Phase 2 구현 시 |
|----------|----------------|
| **해당 없음** (코드 미존재) | **반드시 고려 필수** |

**Phase 2 체크리스트:**
- [ ] 모든 MCP 도구 호출에 `asyncio.to_thread` 또는 `run_in_executor` 적용
- [ ] `MCPToolset.get_tools()` 타임아웃 설정 (연결 실패 시 무한 대기 방지)
- [ ] 도구 목록 캐싱 (반복 호출 지연 방지)
- [ ] 연결 실패 시 재시도 로직 + 예외 처리

**참조:**
- [ADK Performance Guide](https://google.github.io/adk-docs/tools-custom/performance/)
- [GitHub adk-python Issues](https://github.com/google/adk-python/issues)

---

### 2.3 Drive-by RCE Vulnerability (Token Bootstrap)

**감사 판정:** Fail — "HTTP API로 토큰을 발급하면 Drive-by RCE에 취약"

**실제 평가: 부분적으로 타당 — 단, 현재 구현의 방어력이 감사 평가보다 높음**

#### 현재 방어 레이어

[src/adapters/inbound/http/routes/auth.py#L25-L30](src/adapters/inbound/http/routes/auth.py#L25-L30):
```python
origin = request.headers.get("Origin", "")
if not origin.startswith("chrome-extension://"):
    raise HTTPException(status_code=403, ...)
```

| 방어 레이어 | 구현 위치 | 효과 |
|------------|----------|------|
| **CORS** | app.py | `allow_origin_regex` → 일반 웹사이트 `fetch` 차단 |
| **Origin 검증** | auth.py | `/auth/token` 엔드포인트에서 재확인 |
| **토큰 필수** | security.py | 토큰 없이 `/api/*` 접근 불가 |

#### 공격 벡터별 분석

| 공격 벡터 | 현재 방어 | 평가 |
|----------|----------|------|
| 웹사이트 `fetch('localhost:8000/auth/token')` | CORS가 차단 + Origin 검증 | ✅ 방어됨 |
| `curl localhost:8000/auth/token` (로컬 프로세스) | Origin 헤더 위조 가능 | ⚠️ 취약 |
| DNS Rebinding | CORS Origin 검증으로 부분 방어 | ⚠️ 부분 취약 |
| 악성 Chrome Extension | 정상 Extension으로 위장 가능 | ⚠️ 취약 (구조적 한계) |

#### 웹 검증: Localhost 보안 위협

**Oligo Security - "0.0.0.0 Day":**
> "Researchers disclosed a logical vulnerability to all major browsers that enables external websites to communicate with (and potentially exploit) software that runs locally on MacOS and Linux"
[Oligo Security Blog](https://www.oligo.security/blog/0-0-0-0-day-exploiting-localhost-apis-from-the-browser)

**GitHub Blog - Localhost Dangers:**
> "There's a surprising amount of complexity and security risk in this area, and coming changes in browsers may make it even more fragile than it is today"
[GitHub Blog](https://github.blog/security/application-security/localhost-dangers-cors-and-dns-rebinding/)

**Chrome Native Messaging vs HTTP:**
[Chrome Native Messaging Docs](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)
> "Unlike WebSockets, this API cannot be used by websites, so the application can be certain: any request coming in originates from the browser extension"

[text/plain - Native Messaging](https://textslashplain.com/2020/09/04/web-to-app-communication-the-native-messaging-api/)
> "Using WebSockets is unnecessary — browsers implement native messaging API which is meant specifically to let extensions and their applications communicate"

#### 감사 주장 vs 실제

**감사 주장:** "Security Score 45/100"
**재평가:** 과소평가 — 브라우저 기반 공격은 대부분 방어됨

**실제 위협 수준:**
- 브라우저 기반 공격: **낮음** (CORS + Origin 검증)
- 로컬 프로세스 공격: **중간** (데스크톱 앱 환경에서 현실적 시나리오)
- 악성 Extension: **중간** (구조적 한계, 모든 localhost API의 공통 문제)

#### 개선 로드맵

| Phase | 개선안 | 보안 수준 | UX 영향 | 복잡도 |
|-------|--------|:--------:|:------:|:------:|
| **Phase 2** | 토큰 발급 1회 제한 + 콘솔 출력 | 🟡 중간 | 🟢 낮음 | 🟢 낮음 |
| **Phase 2.5** | Extension 설치 시 파일 자동 읽기 | 🟢 높음 | 🟡 중간 | 🟡 중간 |
| **Phase 3+** | Native Messaging 전환 | 🟢 매우 높음 | 🟡 중간 | 🔴 높음 |

#### VS Code Server 패턴 참조

[OpenVSCode Server Discussion #249](https://github.com/gitpod-io/openvscode-server/discussions/249):
```
http://localhost:3000/?tkn=40711257-5e5d-4906-b88f-fe13b1f317b7
```
> 서버 시작 시 토큰을 콘솔에 출력하고 사용자가 URL에 포함시키는 패턴

#### 결론

**단기 조치 (Phase 2):**
- 토큰 발급 횟수 제한 (서버 재시작 시 리셋)
- 서버 시작 시 콘솔에 토큰 출력
- Extension에서 사용자 입력 또는 로컬 파일 읽기

**장기 검토 (Phase 3+):**
- Native Messaging 전환 검토 (보안 vs 복잡도 트레이드오프)
- Offscreen Document + Native Messaging 병행 시 복잡도 급증 주의

**현재 구현 유지 가능:**
- MVP 단계에서 HTTP + Token Handshake는 **합리적 선택**
- 브라우저 기반 공격은 이미 방어됨
- 로컬 프로세스 공격은 Phase 2.5에서 점진적 개선

**참조:**
- [Chrome Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)
- [MDN - Native Messaging](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging)
- [Medium - Native Messaging as Bridge](https://medium.com/fme-developer-stories/native-messaging-as-bridge-between-web-and-desktop-d288ea28cfd7)

---

### 2.4 Dependency Inversion Leakage (외부 예외 누수)

**감사 판정:** Warn — "ADK/LiteLLM 예외가 Domain Layer로 누수될 위험"

**실제 평가: 타당하지만 현재 단계에서는 해당 없음**

#### 현재 상태

- ADK Adapter **미구현** → 실제 코드에서의 누수 없음
- [src/domain/exceptions.py](src/domain/exceptions.py): `LlmRateLimitError`, `EndpointConnectionError` 등 도메인 예외가 이미 정의됨
- Phase 2 구현 시 Adapter 레벨에서 외부 예외 → 도메인 예외 변환 패턴 적용 예정

#### 표준 패턴

```python
# Adapter Layer
try:
    result = await adk_client.run_async(message)
except google.api_core.exceptions.ResourceExhausted as e:
    raise LlmRateLimitError(str(e)) from e
except google.api_core.exceptions.Unauthenticated as e:
    raise LlmAuthenticationError(str(e)) from e
```

#### 결론

- Phase 2 구현 시 자연스럽게 해결 가능
- 현재 조치 불필요
- **헥사고날 아키텍처의 핵심 원칙**이므로 code-reviewer 서브에이전트가 자동 검증 예정

---

### 2.5 Context Explosion (도구 개수 폭발)

**감사 지적:** "단순 개수 제한은 불충분, 동적 토큰 관리 필요"

**실제 평가: MVP에서는 충분, Phase 4 이후 검토**

#### 현재 구현 (문서화)

[docs/implementation-guide.md#23-context-explosion-방지](docs/implementation-guide.md#23-context-explosion-방지):
```python
MAX_ACTIVE_TOOLS = 30
TOOL_TOKEN_WARNING_THRESHOLD = 10000
```

#### 감사 제안 vs 실용성

| 항목 | 감사 제안 | 현실성 평가 |
|------|----------|------------|
| **동적 토큰 계산** | LLM Context Window 여유분에 따라 도구 로드 | Phase 4 영역 (Optional) |
| **Tool Search** | 시맨틱 라우팅으로 관련 도구만 로드 | MCP 스펙도 `defer_loading` 표준화 중 |
| **30개 제한** | 불충분 | MVP에서 합리적 |

#### MCP 스펙 동향

[MCP Transport Future (2025-12)](http://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/):
> "Challenges have emerged at scale: stateful connections force 'sticky' routing that prevents effective auto-scaling"

MCP 자체도 세션 관리 및 도구 로딩 메커니즘을 재설계 중. 현재 단계에서 과도한 최적화는 오버엔지니어링.

#### 결론

- 30개 도구 제한은 MVP에서 충분
- 토큰 기반 동적 관리는 Phase 4 (Optional)
- MCP 스펙 안정화 후 재검토 권장

---

### 2.6 Native Messaging Host 도입 제안

**감사 판정:** Phase 2.5에서 도입 권장
**실제 평가: 기술적으로 타당하지만 시기상조**

#### Native Messaging의 장점

[Chrome Native Messaging Docs](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging):
- 포트 개방 불필요 → DNS Rebinding/Drive-by 공격 원천 차단
- stdio 기반 → 웹사이트에서 접근 불가
- Chrome 공식 권장 패턴

#### 도입의 현실적 어려움

| 이슈 | 설명 | 난이도 |
|------|------|:------:|
| **SSE 스트리밍** | stdio로 메시지 프레이밍 직접 구현 필요 | 🔴 높음 |
| **프로세스 생명주기** | Extension이 Python 프로세스 직접 실행/종료 관리 | 🟡 중간 |
| **플랫폼별 등록** | Windows Registry, macOS plist, Linux 각각 처리 | 🔴 높음 |
| **아키텍처 재설계** | 현재 HTTP 기반 → stdio 기반 전면 변경 | 🔴 매우 높음 |

#### 결론

**현재 HTTP + Token Handshake 유지가 합리적:**
- MVP 관점: 기능 검증이 우선
- 보안 수준: 브라우저 공격은 이미 방어됨
- [docs/risk-assessment.md#44-native-messaging-host](docs/risk-assessment.md#44-native-messaging-host)에서 이미 "보류" 판정

**Phase 3+ 점진적 전환 검토:**
- A2A 통합 완료 후 아키텍처 안정화
- 보안 위협 수준 재평가
- 복잡도 vs 보안 트레이드오프 재검토

---

## 3. 로드맵 분석: 누락/모호/모순

### 3.1 누락 사항

| 항목 | 영향도 | 설명 | 조치 |
|------|:------:|------|------|
| **DI Container 구현 시점** | 🔴 높음 | Phase 1 DoD에 포함 안 됨. `src/config/` 비어있음 | Phase 2 진입 전 스캐폴딩 필수 |
| **FastAPI Lifespan** | 🟡 중간 | `main.py`가 단순 import만 수행. startup/shutdown 미설정 | Phase 2 초기화 패턴 구현 시 필요 |
| **Settings 구현** | 🟡 중간 | `pydantic-settings` + YAML이 문서에만 존재 | DI Container와 함께 구현 |
| **Middleware 순서 테스트** | 🟡 중간 | LIFO 동작에 대한 통합 테스트 없음 | 버그 수정 후 회귀 테스트 추가 |

### 3.2 모호한 부분

| 항목 | 설명 | 개선 방안 |
|------|------|----------|
| **Phase 1.5 DoD 미달** | Roadmap의 Phase 1.5 DoD 체크박스가 [ ] 상태 | DoD 갱신 필요 |
| **Extension 없는 보안 검증** | Extension 미존재 상태에서 Token Handshake E2E 검증 불가 | Phase 2.5에서 통합 테스트 |
| **A2A 통합 범위** | Phase 3의 "Basic Integration"이 구체적으로 어디까지인지 불명확 | Agent Card 교환 + JSON-RPC 기본 호출로 명시화 필요 |

### 3.3 모순

| 항목 | 설명 | 수정 필요 |
|------|------|:--------:|
| **Middleware 주석 vs 실제 동작** | [app.py:15](src/adapters/inbound/http/app.py#L15) 주석이 LIFO 동작과 모순 | ✅ 즉시 |
| **Phase 1 DoD vs 실제** | DI Container가 Phase 1 범위인데 미구현. 단, Fake Adapter로 테스트는 통과 | ⚠️ Phase 2 전 |

---

## 4. 프로젝트 방향성 평가 및 조언

### 4.1 종합 평가: 유지 권장 (계획 수정 불필요)

전체적인 아키텍처 방향(헥사고날, MCP 우선, Extension 기반)은 **건전하며 롤백 불필요**합니다.

### 4.2 즉시 수정 필요 (Phase 2 진입 전)

| 우선순위 | 항목 | 난이도 | 예상 시간 | 파일 |
|:--------:|------|:------:|:--------:|------|
| 🔴 P0 | **Middleware 순서 수정** | 낮음 | 10분 | app.py |
| 🔴 P0 | **Middleware 주석 수정** | 낮음 | 5분 | app.py |
| 🟡 P1 | **DI Container 스캐폴딩** | 중간 | 1시간 | config/container.py, config/settings.py |
| 🟡 P1 | **FastAPI Lifespan 구현** | 낮음 | 30분 | main.py |
| 🟢 P2 | **Phase 1.5 DoD 갱신** | 낮음 | 10분 | docs/roadmap.md |

### 4.3 Phase 2 진입 시 주의사항

| 항목 | 조언 | 참조 |
|------|------|------|
| **ADK MCPToolset** | `get_tools()` 이벤트 루프 충돌, 무한 대기, 반복 호출 지연 이슈 파악 후 타임아웃 + 캐싱 필수 | [#755](https://github.com/google/adk-python/issues/755), [#3788](https://github.com/google/adk-python/issues/3788), [#3237](https://github.com/google/adk-python/issues/3237) |
| **MCP Transport** | Streamable HTTP 우선, SSE는 deprecated. 폴백 전략 유지하되 Streamable HTTP 최우선 | [MCP 2025-06-18 스펙](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) |
| **async 패턴** | 모든 MCP 도구 호출에 `asyncio.to_thread` 또는 `run_in_executor` 적용 | [ADK Performance Guide](https://google.github.io/adk-docs/tools-custom/performance/) |
| **API 버전 추적** | ADK는 API 변경이 빈번. 구현 전 최신 GitHub Issues 확인 필수 | [adk-python](https://github.com/google/adk-python) |

### 4.4 보안 개선 로드맵 (점진적)

```
Phase 2 (즉시)     → 토큰 발급 1회 제한 + 콘솔 출력
                     + 로그에 Extension ID 기록
Phase 2.5 (확장)   → Extension 설치 시 로컬 파일 자동 읽기
                     또는 사용자 토큰 입력 UI
Phase 3+ (선택적)  → Native Messaging 전환 검토
                     (위험-비용-UX 재평가 후)
```

### 4.5 변경 불필요한 부분 (현재 전략 유지)

| 항목 | 이유 |
|------|------|
| **헥사고날 아키텍처** | Domain 순수성 95/100. 과잉 비용 우려는 현 프로젝트 규모에서 비해당 |
| **MCP 우선 전략** | A2A 생태계 미성숙([fka.dev 분석](https://blog.fka.dev/blog/2025-09-11-what-happened-to-googles-a2a/)). MCP 우선 전략 유지 적절 |
| **Offscreen Document** | Service Worker 30초 타임아웃의 현실적 해결책. Native Messaging 전환은 시기상조 |
| **Fake Adapter 패턴** | Mock 대신 Fake는 헥사고날의 핵심 장점. 테스트 격리 완벽 |
| **TDD 워크플로우** | 커버리지 90.84% 달성. 워크플로우 자체는 성공적 |
| **SQLite WAL** | 동시성 처리 완료. PostgreSQL 등 전환 불필요 (MVP 규모) |

---

## 5. 감사 보고서 종합 재평가

### 5.1 항목별 재평가

| 감사 항목 | 감사 판정 | 재평가 | 근거 |
|----------|:--------:|:------:|------|
| **Domain Purity** | Pass | **동의** | 외부 의존성 0건 확인 |
| **Dependency Inversion** | Warn | **동의 (Phase 2 해당)** | Adapter 미구현, 구현 시 주의 필요 |
| **Localhost Safety** | Fail | **부분 동의** | 브라우저 공격 방어됨. 로컬 프로세스만 취약 |
| **MCP Non-blocking** | Fail | **시기상조** | 코드 미존재. 문서에 패턴 준비됨 |
| **CORS Preflight** | Fail | **부분 동의** | OPTIONS 정상. 403 CORS 헤더 누락은 실제 버그 |

### 5.2 감사 Overall Score 재평가

**감사:** B- (Architecture A / Implementation C)
**재평가:** **B+** (Architecture A / Implementation B-)

#### 재평가 근거

**Implementation C → B- 상향 이유:**
- OPTIONS 처리, Origin 검증, 테스트 173개 등 구현 품질 양호
- 미들웨어 순서 버그 1건은 수정 용이 (10분)
- "모래 위의 철옹성" 비유는 과장:
  - 기반 인프라의 핵심 문제(CORS, Blocking)에 대해 **문서화된 대응 패턴 존재**
  - 해당 코드(ADK Adapter) 자체가 **아직 구현 전**
  - 감사가 우려한 이슈는 대부분 **Phase 2 범위**

**Architecture A 유지:**
- 헥사고날 아키텍처 완벽 준수
- Domain 순수성 100%
- Port 기반 테스트 격리 완벽

### 5.3 감사 지적의 타당성 종합

| 타당성 | 항목 수 | 비율 |
|:------:|:-------:|:----:|
| ✅ **타당** | 2 | 33% |
| ⚠️ **부분 타당** | 2 | 33% |
| ❌ **시기상조/과장** | 2 | 33% |

---

## 6. 최종 권고사항

### 6.1 즉시 행동 (Phase 2 진입 전)

#### P0: Critical (24시간 내)

```bash
# 1. Middleware 순서 수정
# src/adapters/inbound/http/app.py
app.add_middleware(ExtensionAuthMiddleware)   # 먼저 추가 (innermost)
app.add_middleware(                            # 나중 추가 (outermost)
    CORSMiddleware,
    allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-Extension-Token", "Content-Type"],
    allow_credentials=False,
)

# 2. 주석 수정
# "Middleware 순서 (중요):
#  LIFO 방식으로 동작 - 나중에 추가한 미들웨어가 먼저 실행됩니다.
#  1. ExtensionAuthMiddleware 먼저 추가 -> innermost (나중에 실행)
#  2. CORSMiddleware 나중 추가 -> outermost (먼저 실행)
#  이유: CORS preflight (OPTIONS) 요청과 403 에러 응답에 CORS 헤더가 포함되어야 합니다."
```

#### P1: High (3일 내)

1. **DI Container 스캐폴딩**
   ```python
   # src/config/container.py
   from dependency_injector import containers, providers
   from .settings import Settings

   class Container(containers.DeclarativeContainer):
       config = providers.Configuration()
       settings = providers.Singleton(Settings)
       # Phase 2에서 adapters 추가 예정
   ```

2. **Settings 구현**
   ```python
   # src/config/settings.py
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       server_host: str = "localhost"
       server_port: int = 8000
       # Phase 2에서 LLM, Storage 설정 추가
   ```

3. **FastAPI Lifespan**
   ```python
   # src/main.py
   from contextlib import asynccontextmanager

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Startup
       print("AgentHub starting...")
       yield
       # Shutdown
       print("AgentHub shutdown")

   app = create_app(lifespan=lifespan)
   ```

#### P2: Medium (1주 내)

1. **Phase 1.5 DoD 갱신** (docs/roadmap.md)
2. **Middleware 통합 테스트 추가**
   ```python
   # tests/integration/test_middleware_order.py
   async def test_cors_headers_on_403_response():
       # 토큰 없이 /api/chat 호출 시 403 + CORS 헤더 확인
       ...
   ```

### 6.2 Phase 2 진입 시 (구현 전 체크리스트)

#### ADK/MCP 통합 전 필수 확인

- [ ] [ADK GitHub Issues](https://github.com/google/adk-python/issues) 최신 버전 확인
- [ ] `MCPToolset.get_tools()` 타임아웃 설정 계획
- [ ] 도구 목록 캐싱 전략 수립
- [ ] `asyncio.to_thread` 패턴 적용 위치 파악
- [ ] [MCP 2025-06-18 스펙](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) 재확인

#### 구현 패턴 준수

```python
# DynamicToolset.call_tool() 예시
async def call_tool(self, tool_name: str, arguments: dict) -> Any:
    for toolset in self._mcp_toolsets.values():
        tools = await toolset.get_tools()
        for tool in tools:
            if tool.name == tool_name:
                # 블로킹 방지: 스레드 풀 격리
                return await asyncio.to_thread(
                    lambda: asyncio.run(tool.run_async(arguments, None))
                )
    raise ToolNotFoundError(f"Tool not found: {tool_name}")
```

#### 서브에이전트 호출 계획

| 시점 | 서브에이전트 | 목적 |
|------|-------------|------|
| DynamicToolset 구현 전 | `tdd-agent` | 테스트 우선 작성 (Red-Green-Refactor) |
| ADK Adapter 구현 후 | `hexagonal-architect` | Port 준수 검증 |
| 보안 코드 작성 후 | `security-reviewer` | SSE Zombie Task, 입력 검증 |
| Phase 2 완료 전 | `code-reviewer` | 전체 품질 검토 + PR 준비 |

### 6.3 장기 검토 (Phase 3+)

#### Native Messaging 전환 결정 기준

| 조건 | 현재 | 목표 |
|------|:----:|:----:|
| **위협 수준** | 로컬 프로세스 공격 (중간) | 실제 공격 사례 발생 |
| **사용자 규모** | MVP (10-100명) | 1000명+ |
| **보안 요구사항** | 일반 | 금융/의료 등 고보안 |

**결정 프로세스:**
1. Phase 3 완료 후 보안 감사 재실시
2. 로컬 프로세스 공격 시나리오 위험 재평가
3. Native Messaging 전환 비용-효익 분석
4. UX 영향도 테스트
5. Go/No-Go 결정

#### MCP 스펙 추적

[MCP Blog - Transport Future](http://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/):
> "The planned changes reorient MCP around stateless, independent requests without sacrificing rich features"

**추적 대상:**
- 세션 관리 메커니즘 변경
- `defer_loading` 표준화
- Stateless 전환 일정

#### A2A 생태계 재평가

[fka.dev - What Happened to A2A](https://blog.fka.dev/blog/2025-09-11-what-happened-to-googles-a2a/):
> A2A 생태계 성숙도가 낮음. Google의 지원도 불명확

**재평가 시점:** Phase 3 완료 후 (2026년 Q2 예상)

---

## 7. 참조 자료

### 7.1 공식 문서

| 항목 | URL |
|------|-----|
| **Google ADK** | https://google.github.io/adk-docs/ |
| **MCP Specification** | https://modelcontextprotocol.io/specification/2025-06-18/basic/transports |
| **Chrome Extension** | https://developer.chrome.com/docs/extensions |
| **FastAPI** | https://fastapi.tiangolo.com/ |
| **Starlette** | https://www.starlette.io/ |

### 7.2 핵심 이슈 및 블로그

#### ADK Issues
- [#755 - Event Loop Conflicts](https://github.com/google/adk-python/issues/755)
- [#3788 - Blocking Behavior](https://github.com/google/adk-python/issues/3788)
- [#3237 - get_tools() Latency](https://github.com/google/adk-python/issues/3237)
- [#1267 - Intermittent Errors](https://github.com/google/adk-python/issues/1267)

#### MCP
- [Why MCP Deprecated SSE](https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http/)
- [MCP Transport Future](http://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/)

#### 보안
- [Oligo Security - 0.0.0.0 Day](https://www.oligo.security/blog/0-0-0-0-day-exploiting-localhost-apis-from-the-browser)
- [GitHub Blog - Localhost Dangers](https://github.blog/security/application-security/localhost-dangers-cors-and-dns-rebinding/)

#### FastAPI/CORS
- [FastAPI Discussion #10366](https://github.com/fastapi/fastapi/discussions/10366)
- [Medium - CORS Dilemma](https://medium.com/@saurabhbatham17/navigating-middleware-ordering-in-fastapi-a-cors-dilemma-8be88ab2ee7b)

#### Native Messaging
- [Chrome Docs](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)
- [text/plain - Native Messaging](https://textslashplain.com/2020/09/04/web-to-app-communication-the-native-messaging-api/)
- [Medium - Native Messaging as Bridge](https://medium.com/fme-developer-stories/native-messaging-as-bridge-between-web-and-desktop-d288ea28cfd7)

### 7.3 프로젝트 내부 문서

| 문서 | 경로 |
|------|------|
| **로드맵** | docs/roadmap.md |
| **아키텍처** | docs/architecture.md |
| **구현 가이드** | docs/implementation-guide.md |
| **Extension 가이드** | docs/extension-guide.md |
| **리스크 평가** | docs/risk-assessment.md |

---

## 부록: 감사 보고서 원문 요약

**감사자:** Senior Principal Architect & Google ADK/MCP Specialist
**일자:** 2026-01-29
**대상:** Phase 1.5

### 주요 지적 (6건)

1. **CORS Preflight Rejection** — Middleware 순서 문제
2. **Sync Blocking** — Event Loop 차단 우려
3. **Drive-by RCE** — Token Bootstrap 취약점
4. **Dependency Leakage** — 외부 예외 누수 가능성
5. **Context Explosion** — 도구 개수 제한 불충분
6. **Native Messaging** — HTTP 대신 권장

### 감사 평가

- **Overall Score:** B-
- **Architecture:** A
- **Implementation:** C
- **Purity Score:** 95/100
- **Security Score:** 45/100

### 재평가 후 수정 점수

- **Overall Score:** B+
- **Architecture:** A (변동 없음)
- **Implementation:** B- (C → B-)
- **Purity Score:** 95/100 (변동 없음)
- **Security Score:** 65/100 (45 → 65)

**재평가 근거:**
- 브라우저 기반 공격은 이미 방어됨 (CORS + Origin 검증)
- 로컬 프로세스 공격만 중간 위협 (MVP 단계에서 허용 가능)
- 미들웨어 버그 1건은 수정 용이
- ADK Blocking 우려는 Phase 2 범위 (현재 코드 미존재)

---

**보고서 작성 완료일:** 2026-01-29
**다음 검토 예정일:** Phase 2 완료 후 (2026년 Q2 예상)
