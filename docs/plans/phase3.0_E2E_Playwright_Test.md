# E2E Playwright 테스트 실행 계획

## 📋 개요

**목표**: 7개 E2E Playwright 테스트 전체 실행 (MCP, A2A, LLM 모두 활성화)

**현재 상태**:
- ✅ Extension 빌드 완료 (`extension/.output/chrome-mv3/`)
- ✅ OpenAI API 키 설정 완료 (`.env`)
- ✅ 테스트 코드 구현 완료 (7 scenarios)
- ❌ Playwright 미설치 (차단 이슈)
- ⚠️ MCP server 미실행 (port 9000 필요)

**범위**:
- Playwright 설치 및 설정
- MCP server 실행 (Synapse, port 9000)
- 전체 7개 테스트 실행
- 테스트 결과 문서화

---

## 🎯 테스트 시나리오

| # | 테스트 이름 | 마커 | 의존성 | 상태 |
|---|-------------|------|--------|------|
| 1 | Extension loads and connects | `@e2e_playwright` | Extension, Server | ✅ 준비 |
| 2 | Token exchange on startup | `@e2e_playwright` | Extension, Server | ✅ 준비 |
| 3 | Chat sends and receives | `@e2e_playwright`, `@llm` | + OpenAI API | ✅ 준비 |
| 4 | MCP server registration | `@e2e_playwright`, `@local_mcp` | + MCP server (9000) | ⚠️ 서버 필요 |
| 5 | A2A agent registration | `@e2e_playwright`, `@local_a2a` | + A2A agent (9001) | ✅ 자동 시작 |
| 6 | Conversation persists | `@e2e_playwright`, `@llm` | + OpenAI API | ✅ 준비 |
| 7 | Code block rendering | `@e2e_playwright`, `@llm` | + OpenAI API | ✅ 준비 |

---

## 📝 실행 계획

### Phase 1: 환경 설정 (5분)

#### Step 1.1: Playwright 설치

```bash
# 1. Playwright 패키지 설치
pip install playwright

# 2. Chromium 브라우저 바이너리 설치
playwright install chromium

# 3. 설치 확인
playwright --version
```

**검증**:
```bash
pytest tests/e2e/ --collect-only -m e2e_playwright
```

**예상 출력**: `collected 7 items`

---

#### Step 1.2: MCP Server 실행 (별도 터미널)

**경로**: `C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP`

**실행 방법**:
```bash
# 터미널 1 - MCP Server
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
set SYNAPSE_PORT=9000
python -m synapse
```

**검증**:
```bash
# 터미널 2 - 헬스 체크
curl http://127.0.0.1:9000/health
```

**예상**: 200 OK 응답

---

### Phase 2: 테스트 실행 (2분)

#### Wave 1: 기본 인프라 테스트 (30초)

```bash
pytest tests/e2e/test_playwright_extension.py::test_extension_loads_and_connects tests/e2e/test_playwright_extension.py::test_token_exchange_on_startup -m e2e_playwright -v
```

**검증 포인트**:
- ✅ 서버가 자동으로 localhost:8000에서 시작
- ✅ Chromium 브라우저 창이 열림 (headed mode)
- ✅ Extension이 로드되고 ID가 추출됨
- ✅ Sidepanel에서 "Connected" 상태 표시

**예상 출력**:
```
test_extension_loads_and_connects PASSED
test_token_exchange_on_startup PASSED
==================== 2 passed in 15s ====================
```

---

#### Wave 2: LLM 기능 테스트 (60초)

```bash
pytest tests/e2e/test_playwright_extension.py::test_chat_sends_and_receives tests/e2e/test_playwright_extension.py::test_conversation_persists_across_tabs tests/e2e/test_playwright_extension.py::test_code_block_rendering -m e2e_playwright -v
```

**검증 포인트**:
- ✅ 채팅 입력 및 LLM 응답 수신
- ✅ 탭 전환 시 대화 내용 유지
- ✅ 코드 블록 하이라이팅 적용

**예상 출력**:
```
test_chat_sends_and_receives PASSED
test_conversation_persists_across_tabs PASSED
test_code_block_rendering PASSED
==================== 3 passed in 60s ====================
```

---

#### Wave 3: 외부 서비스 테스트 (20초)

**Test 4 - MCP Server**:
```bash
pytest tests/e2e/test_playwright_extension.py::test_mcp_server_registration_and_tools -m e2e_playwright -v
```

**검증 포인트**:
- ✅ MCP 서버 등록 (`http://127.0.0.1:9000/mcp`)
- ✅ 서버 목록에 표시
- ✅ 도구 목록 확장 가능

---

**Test 5 - A2A Agent**:
```bash
pytest tests/e2e/test_playwright_extension.py::test_a2a_agent_registration -m e2e_playwright -v
```

**검증 포인트**:
- ✅ A2A Echo Agent 자동 시작 (conftest.py)
- ✅ 에이전트 등록 (`http://127.0.0.1:9001`)
- ✅ Agent Card 정보 표시

---

#### 전체 실행 (권장)

모든 Wave가 성공하면:

```bash
pytest tests/e2e/test_playwright_extension.py -m e2e_playwright -v
```

**예상 출력**:
```
test_extension_loads_and_connects PASSED
test_token_exchange_on_startup PASSED
test_chat_sends_and_receives PASSED
test_mcp_server_registration_and_tools PASSED
test_a2a_agent_registration PASSED
test_conversation_persists_across_tabs PASSED
test_code_block_rendering PASSED
==================== 7 passed in 90s ====================
```

---

### Phase 3: 결과 검증 및 문서화 (10분)

#### Step 3.1: 결과 기록

테스트 실행 후 다음 정보 수집:
- 총 테스트 수: 7
- 통과 수: X
- 실패 수: X
- 스킵 수: X
- 실행 시간: Xs
- Playwright 버전
- Chromium 버전

---

#### Step 3.2: 문서 업데이트

**1. `tests/README.md` - E2E 실행 가이드 추가**

위치: `## Examples` 섹션 (line ~215)

추가 내용:
```markdown
# Playwright E2E 테스트 (headed 모드, Extension 빌드 필요)
pytest tests/e2e/test_playwright_extension.py -m e2e_playwright --headed

# Playwright E2E 특정 시나리오
pytest tests/e2e/test_playwright_extension.py::test_extension_loads_and_connects -m e2e_playwright --headed

# MCP 서버 포함 테스트 (별도 터미널에서 MCP 서버 실행 필요)
# Terminal 1: SYNAPSE_PORT=9000 python -m synapse
# Terminal 2:
pytest tests/e2e/test_playwright_extension.py::test_mcp_server_registration_and_tools -m e2e_playwright --headed
```

---

**2. `docs/STATUS.md` - E2E 테스트 결과 추가**

위치: `## 🧪 Test Coverage Summary` 섹션

추가 내용:
```markdown
| E2E Tests (Playwright) | 7 scenarios | - | ✅ |
```

그리고 `## 📅 Recent Milestones` 섹션에:
```markdown
- **2026-01-30**: Phase 3 Part B Complete - E2E Playwright Tests (7/7 passed)
```

---

**3. `docs/plans/phase3.0.md` - Step 9 DoD 완료 체크**

위치: Step 9 DoD 섹션

업데이트:
```markdown
- [x] Playwright 설치 완료
- [x] Wave 1 (기본): 2/2 passed
- [x] Wave 2 (LLM): 3/3 passed
- [x] Wave 3 (외부): 2/2 passed
- [x] 전체 실행: 7/7 passed
- [x] 문서 업데이트 완료
```

---

## 🔍 주요 파일

| 파일 | 용도 | 수정 여부 |
|------|------|----------|
| `tests/e2e/test_playwright_extension.py` | 테스트 시나리오 (7개) | 읽기만 |
| `tests/e2e/conftest.py` | Playwright fixtures | 읽기만 |
| `extension/.output/chrome-mv3/manifest.json` | Extension manifest | 읽기만 |
| `.env` | OpenAI API 키 | 읽기만 |
| `tests/README.md` | 테스트 실행 가이드 | ✏️ 업데이트 |
| `docs/STATUS.md` | 프로젝트 상태 대시보드 | ✏️ 업데이트 |
| `docs/plans/phase3.0.md` | Phase 3 플랜 및 DoD | ✏️ 업데이트 |

---

## ⚠️ 주의사항

### 1. MCP Server 실행 필수

Test 4 실행 전 반드시 별도 터미널에서 MCP 서버 실행:

```bash
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
set SYNAPSE_PORT=9000
python -m synapse
```

**확인 방법**:
```bash
curl http://127.0.0.1:9000/health
```

---

### 2. A2A Agent는 자동 시작

Test 5의 A2A Echo Agent는 `tests/conftest.py`의 `a2a_echo_agent` fixture가 자동으로 시작합니다.

**수동 확인 불필요**, pytest가 알아서 처리

---

### 3. Headed 모드 필수

Chrome Extension은 headless 모드를 지원하지 않습니다.

- 브라우저 창이 실제로 열림
- UI 상호작용을 육안으로 확인 가능
- CI 환경에서는 `xvfb-run` 필요 (향후)

---

### 4. 포트 충돌 주의

테스트 실행 전 포트 확인:

```bash
# Port 8000 (서버) 사용 중인지 확인
netstat -ano | findstr :8000

# Port 9000 (MCP) 사용 중인지 확인
netstat -ano | findstr :9000

# Port 9001 (A2A) 사용 중인지 확인
netstat -ano | findstr :9001
```

충돌 시:
```bash
# Windows
taskkill /F /PID <PID>
```

---

## 🚀 최종 실행 순서

```bash
# === 터미널 1: MCP Server ===
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
set SYNAPSE_PORT=9000
python -m synapse

# === 터미널 2: AgentHub Tests ===
cd C:\Users\sungb\Documents\GitHub\AgentHub

# 1. Playwright 설치
pip install playwright
playwright install chromium

# 2. 설치 확인
pytest tests/e2e/ --collect-only -m e2e_playwright

# 3. Wave 1 실행 (기본)
pytest tests/e2e/test_playwright_extension.py::test_extension_loads_and_connects tests/e2e/test_playwright_extension.py::test_token_exchange_on_startup -m e2e_playwright -v

# 4. Wave 2 실행 (LLM)
pytest tests/e2e/test_playwright_extension.py::test_chat_sends_and_receives tests/e2e/test_playwright_extension.py::test_conversation_persists_across_tabs tests/e2e/test_playwright_extension.py::test_code_block_rendering -m e2e_playwright -v

# 5. Wave 3 실행 (MCP + A2A)
pytest tests/e2e/test_playwright_extension.py::test_mcp_server_registration_and_tools tests/e2e/test_playwright_extension.py::test_a2a_agent_registration -m e2e_playwright -v

# 6. 전체 실행 (모든 Wave 성공 시)
pytest tests/e2e/test_playwright_extension.py -m e2e_playwright -v

# 7. 문서 업데이트 (별도 진행)
```

---

## ✅ 성공 기준

### 필수 (MUST PASS)

- [x] Wave 1: 2/2 passed (Extension, Token)
- [x] Wave 2: 3/3 passed (Chat, Persistence, Code)
- [x] Wave 3: 2/2 passed (MCP, A2A)

### 최종 목표

```
==================== 7 passed in 90s ====================
```

### 문서화 완료

- [x] `tests/README.md` 업데이트
- [x] `docs/STATUS.md` 업데이트
- [x] `docs/plans/phase3.0.md` DoD 체크

---

## 📊 예상 소요 시간

| 단계 | 작업 | 시간 |
|------|------|------|
| 1 | Playwright 설치 | 3-6분 |
| 2 | MCP Server 실행 | 1분 |
| 3 | Wave 1 테스트 | 30초 |
| 4 | Wave 2 테스트 | 60초 |
| 5 | Wave 3 테스트 | 20초 |
| 6 | 전체 재실행 | 90초 |
| 7 | 문서 업데이트 | 10분 |
| **합계** | | **약 20분** |

---

## 📋 실행 결과 (2026-01-31)

### ✅ 테스트 결과

**전체 통과:** 7/7 scenarios (100%)

| Wave | 테스트 | 결과 | 시간 |
|------|--------|:----:|:----:|
| Wave 1 | Extension + Token (2개) | ✅ PASSED | 7.8s |
| Wave 2 | LLM Features (3개) | ✅ PASSED | ~45s |
| Wave 3 | MCP + A2A (2개) | ✅ PASSED | ~22s |
| **Total** | **7 scenarios** | **✅ 7 PASSED** | **30.72s** |

### 회귀 테스트 결과

| 테스트 | 결과 | 세부 |
|--------|:----:|------|
| Extension Vitest | ✅ PASSED | 180/180 tests (100%) |
| Backend pytest | ✅ PASSED | 305/305 tests (100%) |
| Coverage | ✅ PASSED | 90.63% (Target: 80%) |

---

## 🔧 주요 수정 사항

### 1. 테스트 선택자 전략 변경

**문제:** 테스트가 `data-testid` 속성에 의존했으나, Production 코드에 해당 속성이 없음

**해결 방안:** E2E 원칙에 따라 실제 CSS 클래스와 시맨틱 선택자 사용

#### 수정 파일
- `tests/e2e/test_playwright_extension.py`
- `tests/e2e/conftest.py`

#### 수정 내역

| 항목 | Before (data-testid) | After (E2E 원칙) | 이유 |
|------|---------------------|------------------|------|
| 서버 상태 | `[data-testid="server-status"]` | `.server-status` | 실제 CSS 클래스 사용 |
| 메시지 버블 | `[data-testid="message-bubble"][data-role="assistant"]` | `.message-bubble.assistant` | role이 className에 포함됨 |
| 채팅 입력 | `[data-testid="chat-input"]` | `.chat-input input[type="text"]` | 실제 HTML 요소 |
| 전송 버튼 | `[data-testid="send-button"]` | `get_by_role('button', name='Send')` | 시맨틱 선택자 (접근성) |
| 탭 버튼 | `[data-testid="mcp-servers-tab"]` | `get_by_role('button', name='MCP Servers')` | 사용자가 보는 텍스트 |
| MCP URL 입력 | `[data-testid="mcp-url-input"]` | `input[placeholder="MCP Server URL"]` | placeholder 속성 |
| 코드 블록 | `[data-testid="code-block"]` | `.code-block` | 실제 CSS 클래스 |

#### 핵심 원칙

**E2E 테스트는 사용자가 보는 것을 검증해야 함:**
1. ✅ CSS 클래스 (`.message-bubble`, `.server-status`)
2. ✅ 시맨틱 선택자 (`get_by_role`, `get_by_text`)
3. ✅ HTML 속성 (`placeholder`, `type`)
4. ❌ 테스트 전용 속성 (`data-testid`, `data-role`)

### 2. A2A Echo Agent Fixture 연결

**문제:** E2E conftest가 A2A Echo Agent fixture를 사용하지 않아 A2A 테스트 실패

**해결:**
```python
# tests/e2e/conftest.py
@pytest.fixture
def browser_context(
    extension_path: Path,
    server_process: subprocess.Popen,
    a2a_echo_agent: str  # ← 추가
) -> tuple[BrowserContext, str]:
```

pytest가 자동으로 `tests/conftest.py`의 `a2a_echo_agent` fixture를 실행하여 A2A 에이전트를 시작합니다.

---

## 💡 향후 반영 방안

### Phase 4 권장사항 (선택적)

**Option A: 현재 상태 유지 (권장)**
- ✅ Production 코드 불변
- ✅ E2E 원칙 준수
- ⚠️ CSS 리팩토링 시 테스트도 업데이트 필요

**Option B: 시맨틱 HTML + 접근성 강화**
```tsx
// 컴포넌트에 의미있는 속성 추가
<div
  className={`message-bubble ${message.role}`}
  role="article"  // 시맨틱 HTML
  aria-label={`Message from ${message.role}`}  // 접근성
>
```

```python
# 테스트에서 시맨틱 선택자 사용
assistant_message = sidepanel.locator('[role="article"][aria-label*="assistant"]')
```

**장점:**
- 접근성 향상 (스크린 리더 지원)
- 테스트 안정성 향상
- 웹 표준 준수

**단점:**
- Production 코드 수정 필요
- Phase 4에서 진행 권장

### 테스트 유지보수 가이드

**CSS 리팩토링 시:**
1. Component 클래스명 변경 → 테스트 selector 업데이트
2. 버튼 텍스트 변경 → `get_by_role('button', name='...')` 업데이트
3. placeholder 변경 → `input[placeholder="..."]` 업데이트

**예시:**
```python
# 클래스 변경: .server-status → .connection-status
# tests/e2e/test_playwright_extension.py 수정 필요
status = sidepanel.locator('.connection-status')  # 업데이트
```

---

*계획 작성일: 2026-01-30*
*실행 완료일: 2026-01-31*
*Phase 3 Part B - Step 9 실행 완료*
