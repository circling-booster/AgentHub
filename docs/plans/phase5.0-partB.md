# Phase 5 Part B: MCP Server Authentication (Steps 5-8)

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Part A Complete (A2A 검증 완료)
> **목표:** MCP 서버 연결 시 Header/API Key/OAuth 2.1 인증 지원
> **예상 테스트:** ~18 신규 (backend + extension)
> **실행 순서:** Step 5 → Step 6 → Step 7 → Step 8

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **5** | AuthConfig Domain Entity | ⬜ |
| **6** | Authenticated MCP Connection | ⬜ |
| **7** | MCP Registration API with Auth | ⬜ |
| **8** | OAuth 2.1 Flow (Hybrid) | ⬜ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

---

## Part B Prerequisites

- [ ] Part A Complete (A2A 검증 완료)
- [ ] 기존 테스트 전체 통과

### Step별 검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 6 시작 | ADK StreamableHTTPConnectionParams headers 지원 여부 | Web search |
| 6 시작 | MCP Python SDK 인증 패턴 확인 | Web search |
| 8 시작 | OAuth 2.1 MCP 스펙 확인 | Web search |
| 8 시작 | melon MCP 서버 OAuth 엔드포인트 확인 | Web search |

---

## Step 5: AuthConfig Domain Entity

**목표:** MCP 서버 인증 설정을 위한 도메인 엔티티 추가

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/auth_config.py` | NEW | AuthConfig dataclass (순수 Python) |
| `src/domain/entities/endpoint.py` | MODIFY | `auth_config: AuthConfig \| None = None` 필드 추가 |
| `tests/unit/domain/entities/test_auth_config.py` | NEW | AuthConfig 엔티티 테스트 |

**핵심 설계:**
```python
# src/domain/entities/auth_config.py
from dataclasses import dataclass, field

@dataclass
class AuthConfig:
    """MCP 서버 인증 설정 (순수 Python, 도메인 레이어)"""
    auth_type: str = "none"  # "none" | "header" | "api_key" | "oauth2"

    # Header Auth
    headers: dict[str, str] = field(default_factory=dict)

    # API Key Auth
    api_key: str = ""
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"  # "Bearer", "ApiKey", "" (raw)

    # OAuth 2.1
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""
    oauth2_token_url: str = ""
    oauth2_authorize_url: str = ""
    oauth2_scope: str = ""
    oauth2_access_token: str = ""
    oauth2_refresh_token: str = ""
    oauth2_token_expires_at: float = 0.0

    def get_auth_headers(self) -> dict[str, str]:
        """인증 헤더 생성"""
        if self.auth_type == "header":
            return dict(self.headers)
        elif self.auth_type == "api_key":
            prefix = f"{self.api_key_prefix} " if self.api_key_prefix else ""
            return {self.api_key_header: f"{prefix}{self.api_key}"}
        elif self.auth_type == "oauth2" and self.oauth2_access_token:
            return {"Authorization": f"Bearer {self.oauth2_access_token}"}
        return {}
```

**TDD 순서:**
1. RED: `test_auth_config_none_returns_empty_headers`
2. RED: `test_auth_config_header_returns_custom_headers`
3. RED: `test_auth_config_api_key_returns_bearer_header`
4. RED: `test_auth_config_oauth2_returns_access_token_header`
5. GREEN: AuthConfig 구현
6. REFACTOR: 필요 시 정리

**DoD:**
- [ ] 4개 인증 타입별 헤더 생성 검증
- [ ] Endpoint 엔티티에 auth_config 필드 추가
- [ ] 기존 Endpoint 테스트 regression 없음

---

## Step 6: Authenticated MCP Connection

**목표:** DynamicToolset의 MCP 연결 시 인증 헤더 전달

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/dynamic_toolset.py` | MODIFY | `_create_mcp_toolset()` 에 auth headers 전달 |
| `tests/unit/adapters/test_mcp_auth.py` | NEW | 인증 연결 테스트 |

**핵심 설계:**
```python
# dynamic_toolset.py 변경
async def _create_mcp_toolset(self, url: str, auth_config: AuthConfig | None = None) -> MCPToolset:
    headers = auth_config.get_auth_headers() if auth_config else {}

    # 1. Streamable HTTP (headers 전달)
    try:
        toolset = MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=url,
                timeout=120,
                headers=headers,  # 인증 헤더 주입
            ),
        )
        await toolset.get_tools()
        return toolset
    except Exception:
        pass

    # 2. SSE fallback (headers 전달)
    # ...
```

**웹 검색 필수:** `StreamableHTTPConnectionParams`가 `headers` 파라미터를 지원하는지 확인. 미지원 시 대안:
- MCP Python SDK `ClientSession` 사용
- httpx 커스텀 transport 래핑

**TDD 순서:**
1. RED: `test_create_toolset_passes_auth_headers`
2. RED: `test_create_toolset_no_auth_default`
3. RED: `test_api_key_header_in_request`
4. RED: `test_oauth_token_header_in_request`
5. RED: `test_invalid_auth_type_raises`
6. GREEN: dynamic_toolset.py 수정
7. REFACTOR: auth 관련 메서드 분리

**DoD:**
- [ ] 인증 헤더가 MCP 서버 요청에 포함되는지 검증
- [ ] 인증 없는 기존 서버도 정상 동작 (regression-free)

---

## Step 7: MCP Registration API with Auth

**목표:** MCP 서버 등록 API에 인증 설정 추가, Extension UI 반영

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/inbound/http/schemas/mcp.py` | MODIFY | `AuthConfigSchema` 추가, RegisterRequest에 포함 |
| `src/adapters/inbound/http/routes/mcp.py` | MODIFY | auth_config → Endpoint.auth_config 연결 |
| `extension/lib/types.ts` | MODIFY | `AuthConfig` TypeScript 타입 추가 |
| `extension/entrypoints/sidepanel/` | MODIFY | MCP 서버 등록 폼에 인증 필드 추가 |
| `tests/integration/adapters/test_mcp_auth_api.py` | NEW | 인증 API 통합 테스트 |

**API 스키마 변경:**
```python
# schemas/mcp.py
class AuthConfigSchema(BaseModel):
    auth_type: str = "none"
    headers: dict[str, str] = {}
    api_key: str = ""
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"

class RegisterMcpServerRequest(BaseModel):
    url: str
    name: str = ""
    auth: AuthConfigSchema | None = None  # NEW
```

**TDD 순서:**
1. RED: `test_register_mcp_with_api_key_via_api`
2. RED: `test_register_mcp_with_custom_headers_via_api`
3. RED: `test_register_mcp_without_auth_backwards_compatible`
4. GREEN: schemas, routes, Extension UI 수정

**DoD:**
- [ ] API로 인증 설정 포함한 MCP 서버 등록 가능
- [ ] Extension UI에 인증 입력 필드 추가
- [ ] 인증 없는 기존 등록도 정상 동작

---

## Step 8: OAuth 2.1 Flow (Hybrid)

**목표:** MCP 서버가 OAuth 2.1 인증을 요구하는 경우 지원

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/services/oauth_service.py` | NEW | OAuthService (토큰 검증, 갱신 로직) |
| `src/domain/ports/outbound/oauth_port.py` | NEW | OAuthPort (토큰 교환 인터페이스) |
| `src/adapters/outbound/oauth/oauth_adapter.py` | NEW | httpx 기반 OAuth 구현 |
| `src/adapters/inbound/http/routes/oauth.py` | NEW | OAuth authorize/callback 엔드포인트 |
| `extension/lib/oauth.ts` | NEW | OAuth 플로우 시작 (새 탭 열기 or chrome.identity) |
| `tests/unit/domain/services/test_oauth_service.py` | NEW | OAuth 서비스 단위 테스트 |
| `tests/integration/adapters/test_oauth_flow.py` | NEW | OAuth 통합 테스트 |
| `src/config/settings.py` | MODIFY | OAuthSettings 추가 |

**OAuth Flow (Hybrid):**
```
1. Extension "Connect OAuth" 클릭
   ↓
2-A. Backend Path (기본):
   Extension → GET /oauth/authorize?server_id={id}
   Backend → 302 Redirect → OAuth Provider
   User → 로그인/승인
   Provider → localhost:8000/oauth/callback?code=xxx&state=yyy
   Backend → code → access_token 교환
   Backend → AuthConfig에 토큰 저장
   Backend → 브라우저에 성공 페이지 표시
   ↓
2-B. chrome.identity Path (보조):
   Extension → chrome.identity.launchWebAuthFlow({url: authorize_url})
   User → 로그인/승인
   Extension → access_token 수신
   Extension → POST /api/mcp/servers/{id}/auth/token
   Backend → AuthConfig에 토큰 저장
```

**핵심 설계:**
```python
# src/domain/services/oauth_service.py
class OAuthService:
    """OAuth 2.1 도메인 로직 (순수 Python)"""

    def build_authorize_url(self, auth_config: AuthConfig, state: str) -> str:
        """Authorization URL 생성"""
        params = {
            "client_id": auth_config.oauth2_client_id,
            "redirect_uri": f"http://localhost:8000/oauth/callback",
            "response_type": "code",
            "scope": auth_config.oauth2_scope,
            "state": state,
        }
        return f"{auth_config.oauth2_authorize_url}?{urlencode(params)}"

    def is_token_expired(self, auth_config: AuthConfig) -> bool:
        """토큰 만료 여부 (30초 여유)"""
        return time.time() > (auth_config.oauth2_token_expires_at - 30)

    def needs_refresh(self, auth_config: AuthConfig) -> bool:
        """갱신 필요 여부"""
        return (self.is_token_expired(auth_config)
                and bool(auth_config.oauth2_refresh_token))
```

**TDD 순서:**
1. RED: `test_build_authorize_url`
2. RED: `test_is_token_expired`
3. RED: `test_oauth_callback_exchanges_code`
4. RED: `test_token_auto_refresh`
5. RED: `test_invalid_state_rejected`
6. RED: `test_melon_mcp_oauth` (integration, skippable)
7. GREEN: OAuthService, OAuthAdapter, routes 구현
8. REFACTOR: 에러 핸들링 개선

**DoD:**
- [ ] OAuth authorize → callback → token 교환 전체 흐름 동작
- [ ] 토큰 만료 시 자동 갱신
- [ ] 잘못된 state 파라미터 거부
- [ ] Extension에서 OAuth 시작 UI 동작
- [ ] (선택) melon MCP 서버와 실제 OAuth 테스트

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 6 시작 | Web search (ADK headers) | StreamableHTTPConnectionParams headers 지원 확인 |
| Step 8 시작 | Web search (MCP OAuth 2.1) | MCP OAuth 스펙 확인 |
| Step 8 시작 | Web search (melon MCP) | melon MCP 서버 OAuth 엔드포인트 확인 |
| Step 5-8 구현 | `/tdd` | TDD Red-Green-Refactor |
| Step 8 완료 | security-reviewer | OAuth 보안 검토 |

---

## 커밋 정책

```
# 중간 커밋 (Step 5-6 완료 후)
feat(phase5): Step 5-6 - MCP authentication (AuthConfig + Authenticated connection)

# 마지막 커밋 (Step 7-8 완료 후)
feat(phase5): Step 7-8 - MCP auth API + OAuth 2.1 flow
docs(phase5): Part B complete - MCP Authentication
```

---

## Part B Definition of Done

### 기능
- [ ] Header/API Key 인증으로 MCP 서버 등록 가능
- [ ] OAuth 2.1 인증 플로우 동작 (authorize → callback → token)
- [ ] 토큰 자동 갱신 동작
- [ ] Extension UI에 인증 설정 입력 가능

### 품질
- [ ] Backend 18+ 테스트 추가
- [ ] Coverage >= 90% 유지
- [ ] OAuth 보안 검토 완료

### 문서
- [ ] Part B progress checklist 업데이트

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| ADK headers 미지원 | 🟡 | MCP Python SDK 직접 사용 또는 httpx 래핑 |
| melon MCP 서버 접근 불가 | 🟡 | Mock OAuth provider로 테스트 |
| OAuth state 검증 보안 | 🟡 | CSRF 토큰 + 만료 시간 설정 |
| OAuth 토큰 저장 보안 | 🟡 | 메모리 + 암호화된 SQLite 저장 |

---

*Part B 계획 작성일: 2026-01-31*
