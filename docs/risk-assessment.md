# AgentHub 리스크 평가 및 완화 전략

> 아키텍처 감사 보고서 검토 결과 및 권장 완화책

**작성일:** 2026-01-28
**검증 방법:** 웹 검색 기반 2026년 스펙 확인

---

## 1. 평가 요약

외부 아키텍처 감사 보고서를 검토한 결과, 일부 지적은 타당하나 일부는 현 계획 단계에서 과잉 또는 시기상조로 판단됩니다.

### 판정 분류

| 분류 | 설명 | 항목 수 |
|------|------|:---:|
| **즉시 반영** | 초기 설계에 필수 반영 | 4 |
| **문서화** | 위험 인지, 해당 Phase에서 대응 | 2 |
| **보류** | 시기상조 또는 오버엔지니어링 | 4 |
| **참고** | 유효하나 현재 전략 유지 | 1 |

---

## 2. 즉시 반영 항목 (Critical)

### 2.1 비동기 블로킹 병목 (Synchronous Bridging)

**문제:**
Python `asyncio`는 단일 스레드 이벤트 루프 기반. MCP 도구 중 동기식 I/O나 CPU 집약적 작업이 있으면 메인 루프가 차단되어 SSE 스트리밍이 중단될 수 있음.

**완화책:**
```python
# 모든 MCP tools/call 실행 시 필수 적용
import asyncio

async def call_tool(self, tool_name: str, arguments: dict) -> Any:
    """동기 블로킹 방지를 위한 스레드 격리"""
    def _blocking_call():
        return tool.run(arguments)

    # 별도 스레드에서 실행
    return await asyncio.to_thread(_blocking_call)
```

**적용 위치:** `DynamicToolset.call_tool()`, 모든 MCP 도구 실행 경로

---

### 2.2 Localhost 보안 (Drive-by RCE Attack)

**문제:**
`localhost:8000` 포트가 열려 있으면, 악성 웹사이트의 스크립트가 `fetch('http://localhost:8000/api/tools/call')` 시도 가능. 파일 삭제 등 위험한 MCP 도구 실행 위험.

**완화책:**

1. **Token Handshake:**
```python
# 서버 시작 시 난수 토큰 생성
import secrets
EXTENSION_TOKEN = secrets.token_urlsafe(32)

# 모든 API 요청에 토큰 검증
@app.middleware("http")
async def verify_extension_token(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        token = request.headers.get("X-Extension-Token")
        if token != EXTENSION_TOKEN:
            return JSONResponse(status_code=403, content={"error": "Unauthorized"})
    return await call_next(request)
```

2. **Strict CORS:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://<YOUR_EXTENSION_ID>"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["X-Extension-Token", "Content-Type"],
)
```

3. **Extension 초기화 시 토큰 교환:**
```typescript
// background.ts - 서버 시작 후 토큰 수신
const response = await fetch('http://localhost:8000/auth/token', {
  method: 'POST',
  body: JSON.stringify({ extensionId: chrome.runtime.id })
});
const { token } = await response.json();
await chrome.storage.session.set({ extensionToken: token });
```

**적용 위치:** FastAPI 미들웨어, Extension background.ts

---

### 2.3 Context Explosion (비용 폭탄)

**문제:**
50개 이상의 도구를 등록하면 시스템 프롬프트가 컨텍스트 윈도우를 초과하거나 토큰 비용이 급증.

**완화책:**

1. **도구 개수 제한 및 경고:**
```python
MAX_ACTIVE_TOOLS = 30
TOOL_TOKEN_WARNING_THRESHOLD = 10000  # 약 10k 토큰

async def add_mcp_server(self, endpoint: Endpoint) -> list[Tool]:
    tools = await toolset.get_tools()

    total_tools = sum(len(t) for t in self._tool_cache.values()) + len(tools)
    if total_tools > MAX_ACTIVE_TOOLS:
        raise ToolLimitExceededError(
            f"Active tools ({total_tools}) exceed limit ({MAX_ACTIVE_TOOLS}). "
            "Consider removing unused MCP servers."
        )

    # 도구 정의 토큰 추정
    tool_tokens = estimate_tool_tokens(tools)
    if tool_tokens > TOOL_TOKEN_WARNING_THRESHOLD:
        logger.warning(f"Tool definitions use ~{tool_tokens} tokens")
```

2. **향후 Tool Search 구현 준비:**
   - MCP 스펙의 `defer_loading: true` 옵션 활용 계획
   - 동적 도구 로딩 아키텍처 고려

**적용 위치:** `DynamicToolset.add_mcp_server()`

---

### 2.4 SSE Zombie Tasks

**문제:**
클라이언트(Extension)가 연결을 끊어도 서버의 `yield` 제너레이터가 계속 실행되어 리소스 낭비.

**완화책:**
```python
from fastapi import Request
from fastapi.responses import StreamingResponse

@router.post("/stream")
async def chat_stream(request: Request, body: ChatRequest):
    async def generate():
        try:
            async for chunk in orchestrator.chat(body.conversation_id, body.message):
                # 클라이언트 연결 확인
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping stream")
                    break
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        except asyncio.CancelledError:
            # 연결 해제 시 정리 로직
            logger.info("Stream cancelled, cleaning up")
            await orchestrator.cancel_current_operation()
            raise
        finally:
            # 리소스 정리 보장
            pass

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**적용 위치:** 모든 SSE 스트리밍 엔드포인트

---

## 3. 문서화 항목 (해당 Phase에서 대응)

### 3.1 DB 마이그레이션 (Schema Drift)

**시점:** Phase 3 (Desktop Packaging)

**문제:**
데스크톱 앱 업데이트 시 DB 스키마 변경으로 실행 불가 또는 데이터 손실 가능.

**계획:**
- Alembic 또는 경량 마이그레이션 스크립트 내장
- 앱 시작 시 버전 체크 및 자동 마이그레이션
- 마이그레이션 실패 시 Safe Mode 부팅 (백업 후 초기화)

### 3.2 Desktop Packaging 어려움

**시점:** Phase 3

**문제:**
- PyInstaller 바이너리의 백신 오탐지
- C-Extension 라이브러리 호환성

**계획:**
- CI/CD에 Code Signing 포함
- VirusTotal 검사 자동화
- 오탐지 발생 시 벤더 화이트리스팅 요청 프로세스

---

## 4. 보류 항목 (시기상조/오버엔지니어링)

### 4.1 MCP vs A2A 모델 불일치

**판단:** 현재 "MCP 우선, A2A 선택적" 전략이 이미 적절함.

**원 권장:** "Unified Capability Model"로 Tool/Agent 추상화
**보류 이유:** MVP 단계에서 불필요한 복잡성. A2A 통합 시(Phase 3+) 재검토.

### 4.2 ADK 추상화 누수 (Double Validation)

**판단:** 실제 테스트 없이 추측 수준.

**원 권장:** LLM에 Raw JSON Schema 주입 + Pydantic 재검증
**보류 이유:** ADK가 JSON Schema를 정상 전달하는지 먼저 테스트 필요. 문제 발생 시 대응.

### 4.3 MCP Sampling 보안

**판단:** Sampling 기능은 MVP 범위 외.

**원 권장:** Human-in-the-loop 승인 팝업
**보류 이유:** Sampling 기능 구현 시 검토. 단, **MCP 스펙에서도 human review 권장**하므로 참고.

### 4.4 Native Messaging Host

**판단:** Offscreen Document로 대부분 케이스 커버 가능.

**원 권장:** Service Worker 타임아웃 근본 해결
**보류 이유:** 상당한 아키텍처 변경 필요. 장기 대안으로만 인지.

---

## 5. 참고 항목

### 5.1 Hexagonal Architecture 오버헤드

**판단:** 부분 타당하나 현재 설계 유지.

**분석:**
- MCP, A2A, 다양한 LLM 연동이 핵심인 프로젝트에서 어댑터 분리는 유효
- 단, 엄격한 DTO 매핑보다 실용적 접근 권장
- Domain Exception → HTTP 변환 시 원본 에러 정보 보존 주의

---

## 6. 검증 출처

| 항목 | 출처 |
|------|------|
| MCP Streamable HTTP | [MCP Transports Spec](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) |
| MCP Sampling 보안 | [MCP Blog - Transport Future](https://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/) |
| A2A 채택 현황 | [fka.dev](https://blog.fka.dev/blog/2025-09-11-what-happened-to-googles-a2a/), [Google Developers Blog](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) |
| ADK 버전 | [google-adk PyPI](https://pypi.org/project/google-adk/) |
| Offscreen Document | [Chrome Offscreen API](https://developer.chrome.com/docs/extensions/reference/api/offscreen) |
| CORS Best Practices | [Markaicode - CORS 2025](https://markaicode.com/cors-misconfiguration-breaches-2025/) |

---

## 7. 다음 단계

1. **즉시:** `implementation-guide.md`에 완화책 코드 패턴 추가
2. **Phase 1:** 보안 토큰 핸드셰이크 구현
3. **Phase 2:** SSE 연결 해제 처리 검증
4. **Phase 3:** DB 마이그레이션, 패키징 대응

---

*문서 생성일: 2026-01-28*
