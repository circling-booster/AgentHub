# Phase 2.5 Chrome Extension 수동 검증 가이드

> **목적:** Extension과 서버 연동을 브라우저에서 직접 테스트하여 DoD 충족 확인

**작성일:** 2026-01-30
**Phase:** 2.5 (Chrome Extension)

---

## 역할 분담

### 🤖 Claude가 수행 (자동화 가능)

| 작업 | 명령어/도구 |
|------|-----------|
| **서버 시작** | `uvicorn src.main:app --host localhost --port 8000` |
| **Extension 빌드** | `cd extension && npm run build` |
| **MCP 테스트 서버 시작** | `SYNAPSE_PORT=9000 python -m synapse` (선택적) |
| **로그 확인** | 서버 콘솔, Extension DevTools Console |
| **문제 디버깅** | 에러 메시지 분석, 코드 수정 |
| **자동 테스트 실행** | `pytest tests/e2e/`, `npx vitest run` |

### 👤 사용자가 수행 (수동 필수)

| 작업 | 이유 |
|------|------|
| **Chrome에서 Extension 로드** | 브라우저 UI 조작 필요 |
| **Sidepanel 열기 및 채팅 입력** | 실제 UI 인터랙션 |
| **응답 표시 확인** | 시각적 검증 (텍스트 스트리밍) |
| **MCP 서버 등록 UI 조작** | 입력 필드, 버튼 클릭 |
| **브라우저 재시작** | 토큰 재발급 테스트 |
| **30초+ 긴 응답 테스트** | Offscreen Document 동작 확인 |
| **검증 결과 피드백** | 각 항목 Pass/Fail 보고 |

---

## 사전 준비 (Claude가 수행)

### 1. 서버 시작

```bash
# AgentHub 루트 디렉토리에서
uvicorn src.main:app --host localhost --port 8000
```

**확인 사항:**
- [x] 서버 로그에 "Application startup complete" 출력
- [x] `http://localhost:8000/health` 접속 시 `{"status":"healthy"}` 반환

### 2. Extension 빌드

```bash
cd extension
npm run build
# 또는 개발 모드: npm run dev (watch mode)
```

**확인 사항:**
- [x] `extension/.output/chrome-mv3/` 디렉토리 생성
- [x] `manifest.json` 파일 존재 확인
- [x] 빌드 에러 없음

### 3. (선택) MCP 테스트 서버 시작

```bash
# Synapse 서버 (MCP 구현체)
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
SYNAPSE_PORT=9000 python -m synapse
```

**확인 사항:**
- [x] `http://127.0.0.1:9000/mcp` 접속 가능
- [x] 도구 목록 응답 확인

---

## 수동 검증 체크리스트 (사용자 수행)

### 검증 1: Extension 설치 및 토큰 교환

**절차:**

1. Chrome 브라우저 열기
2. 주소창에 `chrome://extensions/` 입력
3. 우측 상단 "개발자 모드" 활성화
4. "압축해제된 확장 프로그램을 로드합니다" 클릭
5. `AgentHub/extension/.output/chrome-mv3` 폴더 선택
6. Extension 로드 완료

**확인 사항:**

- [ ] Extension 설치 성공 (아이콘 표시)
- [ ] 서버 콘솔에 `POST /auth/token` 요청 로그 확인
- [ ] 서버 응답: `200 OK` (토큰 발급 성공)

**디버깅 (에러 발생 시):**

- Extension DevTools 열기: `chrome://extensions/` → Extension 카드 → "서비스 워커" 링크 클릭
- Console 탭에서 에러 메시지 확인
- 네트워크 탭에서 `/auth/token` 요청/응답 확인

---

### 검증 2: Sidepanel 채팅 기본 동작

**절차:**

1. Chrome 우측 상단 Extension 아이콘 클릭 (또는 Sidepanel 자동 열림)
2. Sidepanel에서 "Chat" 탭 확인
3. 입력 필드에 "Hello" 입력 후 Enter

**확인 사항:**

- [ ] 입력 필드가 비활성화됨 (스트리밍 중)
- [ ] Assistant 메시지 버블이 생성됨
- [ ] 텍스트가 한 글자씩 스트리밍으로 표시됨 (타이핑 효과)
- [ ] 스트리밍 완료 후 입력 필드 다시 활성화
- [ ] 대화 이력에 User/Assistant 메시지 모두 표시

**확인 로그:**

- 서버 콘솔: `POST /api/chat/stream` 요청
- Extension Offscreen Console: SSE 이벤트 수신 로그 (선택적)

---

### 검증 3: MCP 도구 호출 결과 표시

**전제 조건:** MCP 테스트 서버가 실행 중이어야 함 (검증 준비 3번)

**절차:**

1. Sidepanel → "MCP Servers" 탭 클릭
2. URL 입력 필드에 `http://127.0.0.1:9000/mcp` 입력
3. "Register" 버튼 클릭
4. 서버 목록에 등록된 서버 표시 확인
5. "Show Tools" 버튼 클릭 → 도구 목록 펼쳐짐
6. "Chat" 탭으로 돌아가기
7. 입력 필드에 도구를 호출할 수 있는 메시지 입력 (예: "What tools do you have?")

**확인 사항:**

- [ ] MCP 서버 등록 성공
- [ ] 도구 목록이 UI에 표시됨 (예: `get_time`, `calculate` 등)
- [ ] 채팅에서 LLM이 도구를 인식하고 응답
- [ ] (선택) 도구 실행 로그가 메시지에 표시됨

**확인 로그:**

- 서버 콘솔: `POST /api/mcp/servers` → `200 OK`
- 서버 콘솔: `GET /api/mcp/servers/{id}/tools` → 도구 목록 반환

---

### 검증 4: 브라우저 재시작 후 토큰 재발급

**절차:**

1. Chrome 브라우저 완전 종료 (모든 창 닫기)
2. Chrome 재시작
3. Extension 자동 로드 확인
4. Sidepanel 열기 (Extension 아이콘 클릭)
5. 채팅 입력 시도 (예: "Hi again")

**확인 사항:**

- [ ] 서버 콘솔에 새로운 `POST /auth/token` 요청 로그
- [ ] 토큰 재발급 성공 (`200 OK`)
- [ ] 채팅 정상 동작 (이전 대화 이력은 유지되지 않음 - 새 대화)

**이유:**
- `chrome.storage.session`에 저장된 토큰은 브라우저 종료 시 삭제됨
- Background Service Worker의 `onStartup` 이벤트에서 토큰 재발급

---

### 검증 5: 30초 이상 긴 응답 처리 (Offscreen Document)

**목적:** Service Worker 30초 타임아웃을 Offscreen Document가 우회하는지 확인

**절차:**

1. Sidepanel → "Chat" 탭
2. 입력 필드에 긴 응답을 요청하는 메시지 입력:
   ```
   Please write a detailed explanation of hexagonal architecture in software design, with examples. Make it at least 500 words.
   ```
3. Enter 후 응답 대기 (30초 이상 소요 예상)

**확인 사항:**

- [ ] 스트리밍이 30초 이후에도 계속 진행됨
- [ ] 응답이 중단되지 않고 완료됨
- [ ] Extension Service Worker가 종료되지 않음 (DevTools에서 확인 가능)

**확인 로그:**

- Offscreen Console: SSE 이벤트가 30초+ 동안 계속 수신됨
- 서버 콘솔: 스트림 연결이 끊기지 않음

**실패 시 증상:**
- 30초 후 응답이 갑자기 멈춤
- Extension 에러: "Service worker stopped responding"
- → Offscreen Document가 동작하지 않는 것 (Step 6 구현 확인 필요)

---

### 검증 6: 대화 이력 (Conversation History)

**절차:**

1. 여러 메시지를 주고받아 대화 세션 생성 (최소 3턴)
2. Sidepanel을 닫았다가 다시 열기
3. 또는 새 탭에서 Sidepanel 열기

**확인 사항:**

- [ ] 좌측 사이드바에 대화 목록 표시
- [ ] 대화 클릭 시 이전 메시지 전체 로드
- [ ] 이전 대화를 이어서 새 메시지 입력 가능

**확인 로그:**

- 서버 콘솔: `GET /api/conversations` 호출
- 서버 콘솔: `GET /api/conversations/{id}/messages` 호출

---

### 검증 7: 서버 Health Check 및 재연결

**절차:**

1. Extension이 실행 중인 상태에서 서버 종료 (Ctrl+C)
2. Sidepanel의 서버 상태 표시 확인 (빨강/Unhealthy)
3. 서버 재시작 (`uvicorn ...`)
4. 30초 대기 (Health Check 주기)
5. 서버 상태 표시 확인 (초록/Healthy)
6. 채팅 입력 시도

**확인 사항:**

- [ ] 서버 종료 시 상태 표시가 "Unhealthy"로 변경
- [ ] 서버 재시작 후 자동으로 "Healthy"로 복구
- [ ] 채팅 정상 동작 (토큰 자동 재발급)

**확인 로그:**

- Extension Background Console: Health Check 실패/성공 로그
- 서버 콘솔: `GET /health` 주기적 호출 (30초마다)

---

## 검증 결과 보고 양식

검증 완료 후 아래 양식으로 결과 보고:

```
## Phase 2.5 수동 검증 결과

**검증일:** YYYY-MM-DD
**검증자:** [이름]
**환경:** Chrome [버전], Windows/macOS

### 검증 항목 체크

- [ ] 검증 1: Extension 설치 및 토큰 교환
- [ ] 검증 2: Sidepanel 채팅 기본 동작
- [ ] 검증 3: MCP 도구 호출 결과 표시
- [ ] 검증 4: 브라우저 재시작 후 토큰 재발급
- [ ] 검증 5: 30초 이상 긴 응답 처리
- [ ] 검증 6: 대화 이력
- [ ] 검증 7: 서버 Health Check 및 재연결

### 발견된 이슈

1. [이슈 제목]
   - 재현 방법: ...
   - 예상 동작: ...
   - 실제 동작: ...
   - 에러 로그: ...

### 전체 평가

- [ ] 모든 검증 항목 통과 → Phase 2.5 DoD 충족
- [ ] 일부 실패 → 이슈 수정 필요

### 스크린샷 (선택)

[Sidepanel UI 캡처, 에러 화면 등]
```

---

## 문제 해결 (Troubleshooting)

### 1. Extension이 로드되지 않음

**증상:** "확장 프로그램을 로드하는 중 오류 발생"

**원인:**
- manifest.json 구문 오류
- 빌드 미완료

**해결:**
```bash
cd extension
npm run build
# manifest.json 검증
cat .output/chrome-mv3/manifest.json
```

### 2. 토큰 교환 실패 (403 Forbidden)

**증상:** 서버 응답 `403 Forbidden`

**원인:**
- CORS Origin 불일치
- 서버 보안 미들웨어 설정 오류

**해결:**
- 서버 `src/adapters/inbound/http/app.py`의 CORS 설정 확인:
  ```python
  allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$"
  ```
- Extension ID 확인: `chrome://extensions/` → Extension ID 복사

### 3. 채팅 응답이 표시되지 않음

**증상:** 입력 후 아무 응답 없음

**원인:**
- SSE 스트리밍 에러
- Offscreen Document 미동작

**해결:**
- Extension Offscreen Console 확인:
  - `chrome://extensions/` → Extension → "서비스 워커" → Offscreen 컨텍스트 확인
- 서버 로그 확인: SSE 연결 에러

### 4. MCP 서버 등록 실패

**증상:** "Failed to connect to MCP server" 에러

**원인:**
- MCP 서버 미실행
- URL 오타

**해결:**
- MCP 서버 실행 확인: `curl http://127.0.0.1:9000/mcp`
- URL 정확히 입력 (프로토콜 포함: `http://...`)

---

## 참조

- [Phase 2.5 계획](../plans/phase2.5.md)
- [Extension 개발 가이드](../guides/extension-guide.md)
- [보안 구현 가이드](../guides/implementation-guide.md#9-보안-패턴)
- [Chrome Extension DevTools](https://developer.chrome.com/docs/extensions/mv3/tut_debugging/)

---

*작성일: 2026-01-30*
