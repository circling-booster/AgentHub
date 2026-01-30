# Phase 3: Stability & A2A Integration

> **상태:** 📋 Planned
> **선행 조건:** Phase 2.5 Complete
> **목표:** 장시간 작업 안정성, Extension UI 완성, A2A 기본 통합, E2E 테스트 자동화

---

## 개요

Phase 2.5 수동검증에서 발견된 미구현 항목과 기존 로드맵의 안정성/A2A 과제를 통합한다.

---

## 3.1 Zombie Task Killer (Backend Stability)

**문제:** 클라이언트 연결 해제 시 서버 태스크 계속 실행
**해결:** `Request.is_disconnected()` + `asyncio.Task.cancel()`

- SSE 연결 끊김 감지
- 연결 해제 시 `asyncio.CancelledError` 명시적 처리
- 서버 로그에 "Task Cancelled" 출력 확인

**DoD:**
- [ ] 긴 응답 생성 중 탭 닫기 시 서버 로그에 "Task Cancelled"

---

## 3.2 Async Thread Isolation (Backend Stability)

**문제:** 동기식 MCP 도구 실행 시 메인 이벤트 루프 차단 가능성
**해결:** `asyncio.to_thread()` 래핑

**DoD:**
- [ ] 무거운 도구 실행 중에도 `/health` 즉시 응답

---

## 3.3 Extension UI Polish

> **Phase 2.5 수동검증에서 발견된 미구현 항목**

### 3.3.1 MCP Tools 목록 표시

**현재 상태:** MCP 서버 등록 시 서버 내부에 도구가 로드되지만, Extension UI에 표시되지 않음.

**필요 작업:**
- `extension/lib/api.ts`에 `getServerTools(serverId)` 함수 추가
  - Backend API `GET /api/mcp/servers/{id}/tools` 호출
- `extension/hooks/useMcpServers.ts`에 tools 상태 관리 추가
  - 서버 등록 후 자동으로 tools 조회
- `extension/components/McpServerManager.tsx`에 tools UI 추가
  - 서버별 도구 목록 (expandable/collapsible)
  - 도구명, 설명, input_schema 표시

**참고:**
- Backend API는 이미 완성됨: `GET /api/mcp/servers/{server_id}/tools`
- `extension/lib/types.ts`에 `Tool` 인터페이스 정의 완료
- `useMcpServers.test.ts`에 tools mock 데이터 존재 (line 32)

**DoD:**
- [ ] MCP 서버 등록 후 해당 서버의 도구 목록이 UI에 표시
- [ ] 도구명, 설명이 사용자에게 노출

### 3.3.2 대화 히스토리 유지

**현재 상태:** `useChat.ts`가 React state(`useState`)만 사용. 탭 전환(Chat ↔ MCP Servers) 시 대화 내용 소멸.

**필요 작업:**
- `extension/hooks/useChat.ts` 대화 상태 영속화
  - 방법 A: `chrome.storage.session`에 현재 대화 저장 (탭 전환 시 복원)
  - 방법 B: 서버에서 대화 불러오기 (`GET /api/conversations/{id}/messages`)
- `extension/entrypoints/sidepanel/App.tsx`에 대화 복원 로직 추가
  - 마운트 시 이전 대화 상태 복원

**참고:**
- Backend API 존재: `GET /api/conversations`, `GET /api/conversations/{id}`
- `extension/lib/api.ts`에 `listConversations()` 함수 존재하지만 미호출
- 서버는 대화를 SQLite에 저장 중

**DoD:**
- [ ] Chat → MCP Servers → Chat 전환 시 대화 내용 유지
- [ ] (선택) 대화 목록 UI 및 대화 전환 기능

### 3.3.3 코드 블록 및 UI 개선

- 코드 블록 신택스 하이라이팅
- 도구 실행 로그 아코디언 UI
- 에러 상태 표시 개선

**DoD:**
- [ ] 코드 블록에 하이라이팅 적용
- [ ] 도구 실행 결과가 구조화된 UI로 표시

---

## 3.4 A2A Basic Integration

**현재 상태:** MCP만 지원

**필요 작업:**
- Agent Card 생성 및 교환 (A2A 스펙 준수)
- `to_a2a()` 어댑터로 A2A 서버 노출
- 로컬 A2A Agent Server 연결 테스트

**DoD:**
- [ ] A2A Agent Card 교환 성공
- [ ] A2A 에이전트 호출 기본 동작

---

## 3.5 E2E Tests

**필요 작업:**
- Playwright 기반 Extension E2E 테스트
- Full Flow: Extension → Server → MCP/A2A

**DoD:**
- [ ] E2E 시나리오 통과 (토큰 교환 → 채팅 → MCP 도구 호출)

---

## Phase 2.5 수동검증 버그 수정 이력

> Phase 2.5 수동검증 과정에서 발견 및 수정된 버그 목록 (참고용)

| Bug | 원인 | 수정 파일 | 상태 |
|-----|------|----------|:----:|
| Offscreen 문서 경로 불일치 | WXT가 `offscreen.html`로 빌드하지만 코드는 `offscreen/index.html` 참조 | `extension/lib/constants.ts` | ✅ |
| SSE 요청에 인증 토큰 누락 | `sse.ts`에 `X-Extension-Token` 헤더 미포함 | `extension/lib/sse.ts` | ✅ |
| Offscreen 문서 로딩 레이스 컨디션 | 메시지 전송 시 Offscreen 문서 미준비 | `extension/lib/background-handlers.ts` | ✅ |
| Offscreen에서 `browser.storage.session` 미지원 | Offscreen Document 컨텍스트 제한 | `extension/lib/sse.ts`, `offscreen-handlers.ts`, `background.ts` | ✅ |
| LLM 모델 설정 오류 | `anthropic` 대신 `openai/gpt-4o-mini` 필요 | `src/config/settings.py`, `configs/default.yaml` | ✅ |
| API 키 환경변수 미반영 | pydantic-settings가 os.environ에 설정하지 않음 | `src/adapters/inbound/http/app.py` | ✅ |

---

## DoD (전체)

- [ ] Zombie Task: 긴 응답 중 탭 닫기 시 서버 정리 확인
- [ ] Thread Isolation: 무거운 도구 실행 중 `/health` 응답
- [ ] MCP Tools UI: 등록된 서버의 도구 목록 표시
- [ ] 대화 히스토리: 탭 전환 시 대화 유지
- [ ] UI Polish: 코드 블록 하이라이팅, 도구 실행 UI
- [ ] A2A: Agent Card 교환 성공
- [ ] E2E: Playwright 기본 시나리오 통과
- [ ] 문서: `src/adapters/README.md` A2A 추가, `tests/README.md` E2E 섹션

---

*문서 생성일: 2026-01-30*
*Phase 2.5 수동검증 결과 반영*
