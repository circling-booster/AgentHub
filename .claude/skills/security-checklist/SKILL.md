---
name: security-checklist
description: "AgentHub 프로젝트 보안 리뷰 체크리스트. localhost API의 Drive-by RCE 방지를 위한 Token Handshake, CORS, Extension 보안 패턴 검증. 사용 시점: (1) 보안 관련 코드(미들웨어, 인증, CORS) 작성/수정 후, (2) 새로운 API 엔드포인트 추가 시, (3) Extension ↔ Server 통신 코드 리뷰 시, (4) PR 전 보안 검토. 트리거: 보안, security, token, CORS, auth, middleware, Drive-by RCE"
---

# AgentHub 보안 체크리스트

localhost API의 Drive-by RCE 공격 방지를 위한 보안 검증 체크리스트.
위반 사례와 상세 구현 패턴은 `references/violation-examples.md` 참조.

---

## 1. Token Handshake 패턴

- [ ] `secrets.token_urlsafe(32)`로 토큰 생성 (메모리 전용, 파일/DB 저장 금지)
- [ ] `TokenProvider` 클래스의 lazy 생성 + 싱글톤 패턴 사용
- [ ] `X-Extension-Token` 헤더로 모든 `/api/*` 요청 검증
- [ ] `/auth/token`에서 Origin 검증 (`chrome-extension://` 필수)
- [ ] 토큰 재발급 방지 로직 적용
- [ ] 토큰 불일치 시 403 JSON 응답 반환

핵심 코드 위치: `src/adapters/inbound/http/security.py`

## 2. CORS Configuration

- [ ] `allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$"` 사용
- [ ] `allow_origins=["chrome-extension://*"]` 사용 금지 (작동 안 함)
- [ ] Starlette LIFO 미들웨어 순서 준수:

```python
# 실행 순서: CORS(outermost) -> Auth(innermost) -> Router
# add_middleware는 insert(0,...)이므로 나중 추가 = outermost
app.add_middleware(ExtensionAuthMiddleware)   # 먼저 추가 = innermost
app.add_middleware(CORSMiddleware, ...)       # 나중 추가 = outermost
```

- [ ] `allow_credentials=False` (토큰 기반이므로 쿠키 불필요)
- [ ] `allow_headers`에 `X-Extension-Token`, `Content-Type` 포함
- [ ] 403 에러 응답에도 CORS 헤더 포함 확인

핵심 코드 위치: `src/adapters/inbound/http/app.py`

## 3. Extension Client 보안

- [ ] 토큰을 `chrome.storage.session`에 저장 (`local`/`localStorage` 금지)
- [ ] Extension ID로 Origin 검증 (`chrome.runtime.id`)
- [ ] 모든 API 요청에 `X-Extension-Token` 헤더 자동 주입
- [ ] Content Script에서 직접 localhost API 호출 금지 (Background 경유)
- [ ] Token 교환은 `onStartup`/`onInstalled`에서 1회만 수행

## 4. 인증 제외 경로

- [ ] `EXCLUDED_PATHS`에 공개 경로만 등록:
  - `/health`, `/auth/token`, `/docs`, `/openapi.json`, `/redoc`
- [ ] `OPTIONS` 메서드는 Auth 검증 생략 (CORS preflight)
- [ ] 그 외 모든 `/api/*` 경로는 토큰 검증 필수
- [ ] 새 공개 경로 추가 시 `EXCLUDED_PATHS`에 명시적 등록

핵심 코드 위치: `src/adapters/inbound/http/security.py` (`EXCLUDED_PATHS`)

## 5. PR 전 종합 검증

| 항목 | 검증 |
|------|------|
| Token 없이 `/api/*` 호출 | 403 반환 |
| Token 포함 호출 | 정상 응답 |
| `/health` 토큰 없이 접근 | 200 반환 |
| 잘못된 Origin | CORS 차단 |
| OPTIONS preflight | CORS 헤더 포함 200 |
| 토큰 저장 위치 | 메모리/session만 허용 |

## 참조

- `docs/guides/implementation-guide.md#9-보안-패턴`: 전체 보안 구현 패턴
- `docs/archive/risk-assessment.md#22-localhost-보안`: Drive-by RCE 위험 분석