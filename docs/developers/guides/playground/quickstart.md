# Quickstart

Playground를 로컬 환경에서 실행하는 단계별 가이드입니다.

---

## Prerequisites

- Python 3.10+
- AgentHub 백엔드 설정 완료 (가상환경, 의존성 설치)
- Chrome/Firefox 브라우저
- Git Bash (Windows) 또는 터미널 (Mac/Linux)

---

## Step 1: 환경변수 설정

`.env` 파일에 DEV_MODE 추가:

```bash
DEV_MODE=true
```

⚠️ **경고**: DEV_MODE는 로컬 개발 전용입니다. **절대** 프로덕션 환경에 배포하지 마세요.

**DEV_MODE가 하는 일:**
- CORS: `localhost:*` origin 허용
- Security: Token 인증 우회 (localhost origin만)
- Logging: 추가 디버깅 로그 활성화

---

## Step 2: 백엔드 시작

### Windows (cmd.exe or PowerShell)

```bash
cd c:\Users\sungb\Documents\GitHub\AgentHub
.venv\Scripts\activate
set DEV_MODE=true
uvicorn src.main:app --reload --host localhost --port 8000
```

### Windows (Git Bash)

```bash
cd c:/Users/sungb/Documents/GitHub/AgentHub
source .venv/Scripts/activate
DEV_MODE=true uvicorn src.main:app --reload --host localhost --port 8000
```

### Mac/Linux

```bash
cd ~/Documents/GitHub/AgentHub
source .venv/bin/activate
DEV_MODE=true uvicorn src.main:app --reload --host localhost --port 8000
```

**확인:**
```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

---

## Step 3: Static 서버 시작

**새 터미널 창에서:**

### Windows

```bash
cd c:\Users\sungb\Documents\GitHub\AgentHub
python -m http.server 3000 --directory tests/manual/playground
```

### Mac/Linux

```bash
cd ~/Documents/GitHub/AgentHub
python -m http.server 3000 --directory tests/manual/playground
```

**확인:**
브라우저에서 `http://localhost:3000` 접속
- Health 상태: "Healthy" (녹색) 표시
- 페이지 로드 성공

---

## Step 4: 기능 테스트

### 4.1 Health Check

페이지 로드 시 자동 실행:
- 상단 Health Indicator: ● Healthy (녹색)
- 실패 시 "Backend unreachable" (빨강)

### 4.2 Chat 테스트

1. **Chat** 탭 클릭
2. 메시지 입력: `"Hello, AgentHub!"`
3. **Send** 버튼 클릭
4. 좌측 패널: 사용자/에이전트 메시지 표시
5. 우측 SSE Events 패널:
   - `{"type":"text","content":"..."}`
   - `{"type":"done"}`

### 4.3 MCP 서버 등록

1. **MCP** 탭 클릭
2. Server Name: `test-server`
3. Server URL: `http://localhost:9000` (실제 MCP 서버 필요)
4. **Register** 버튼 클릭
5. 서버 카드 표시 확인
6. **Tools** 버튼 클릭 → 도구 목록 표시

**참고**: MCP 서버가 없으면 등록 실패 (정상 동작)

### 4.4 A2A 에이전트 등록

1. **A2A** 탭 클릭
2. Agent Name: `echo-agent`
3. Agent URL: `http://localhost:7000` (실제 A2A 에이전트 필요)
4. **Register** 버튼 클릭
5. 에이전트 카드 표시 확인

### 4.5 Conversations 관리

1. **Conversations** 탭 클릭
2. **Create Conversation** 버튼 클릭
3. 새 대화 항목 표시
4. **Tool Calls** 탭 클릭 → Tool Calls 목록 표시 (빈 경우 "No tool calls")
5. **Delete** 버튼 클릭 → 대화 삭제

### 4.6 Usage 조회

1. **Usage** 탭 클릭
2. Total Tokens, Total Cost 표시
3. Budget 입력: `100.00`
4. **Set Budget** 버튼 클릭
5. Budget Display: `$100.00` 표시

### 4.7 Workflow 실행

1. **Workflow** 탭 클릭
2. Workflow Name: `Test Workflow`
3. Steps: `[{"name":"step1","type":"task"}]`
4. **Execute** 버튼 클릭
5. 우측 SSE Events 패널:
   - `{"type":"workflow_start",...}`
   - `{"type":"workflow_complete",...}`
6. Workflow Result: `Status: completed`

---

## Troubleshooting

### Health 상태가 "Backend unreachable"

**원인:**
- 백엔드가 실행되지 않음
- DEV_MODE가 활성화되지 않음
- 포트 충돌

**해결:**
1. 백엔드 실행 확인:
   ```bash
   curl http://localhost:8000/health
   ```
2. `.env` 확인: `DEV_MODE=true` 설정
3. 포트 충돌 확인:
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Mac/Linux
   lsof -i :8000
   ```
4. 백엔드 재시작

### CORS 에러 발생

**증상**: Console에 CORS policy 에러

**해결:**
1. `.env` 확인: `DEV_MODE=true` 필수
2. Origin 확인: 반드시 `http://localhost:3000` 사용 (127.0.0.1 안됨)
3. 브라우저 캐시 삭제 (Ctrl+Shift+Delete)
4. 백엔드 재시작

### SSE 연결 실패

**증상**: SSE Events 패널에 이벤트 없음

**해결:**
1. Network 탭 열기 (F12)
2. Filter: "EventStream" 선택
3. `/api/chat/stream` 요청 확인:
   - Status: 200 OK
   - Type: eventsource
4. Response 탭에서 이벤트 데이터 확인
5. 에러 있으면 백엔드 로그 확인

### Static 서버 포트 충돌

**증상**: `python -m http.server 3000` 실행 시 에러

**해결:**
다른 포트 사용:
```bash
python -m http.server 3001 --directory tests/manual/playground
```

`.env` 업데이트:
```bash
ALLOWED_ORIGINS=["http://localhost:3001"]
```

백엔드 재시작 후 `http://localhost:3001` 접속

### MCP/A2A 등록 실패

**원인**: 실제 MCP/A2A 서버가 실행되지 않음

**해결 (Optional):**

**MCP Synapse 서버 시작:**
```bash
cd ~/mcp-servers/synapse
python -m uvicorn server:app --host localhost --port 9000
```

**A2A Echo 에이전트 시작:**
```bash
cd ~/a2a-agents/echo
python -m uvicorn agent:app --host localhost --port 7000
```

**참고**: 로컬에 서버가 없으면 등록 실패는 정상 (Playground 자체는 정상 동작)

---

## Advanced Usage

### E2E 테스트 실행

Playground 전체 플로우 자동 테스트:

```bash
# 가상환경 활성화
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# E2E 테스트 실행
pytest tests/e2e/test_playground.py -v
```

**테스트 포함 내용:**
- Health Check
- Chat SSE Streaming
- MCP/A2A 등록/삭제
- Conversations CRUD + Tool Calls
- Usage/Budget
- Workflow 실행

### JavaScript Unit Tests

프론트엔드 모듈 단위 테스트:

```bash
cd tests/manual/playground
npm install  # 최초 1회만
npm test
```

**Coverage Report:**
```bash
npm test -- --coverage
```

### 개발 워크플로우

1. 백엔드 코드 수정
2. 백엔드 자동 재시작 (uvicorn --reload)
3. 브라우저 새로고침 (Ctrl+R)
4. Playground에서 기능 테스트
5. E2E 테스트로 회귀 확인

---

## Next Steps

- [backend-api.md](backend-api.md) - API 엔드포인트별 테스트 방법
- [sse-streaming.md](sse-streaming.md) - SSE 디버깅 가이드
- [Architecture Overview](../../architecture/README.md) - 시스템 아키텍처 이해

---

*Last Updated: 2026-02-06*
*Version: 1.0*
*Plan: 08_playground*
