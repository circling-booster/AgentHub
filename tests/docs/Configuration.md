# **🔧 Configuration**

## **🌐 Port Allocation**

| 서비스 | 기본 포트 | 환경변수 | 용도 |
| :---- | :---- | :---- | :---- |
| MCP Synapse (no auth) | 9000 | MCP\_TEST\_PORT | 기본 MCP 테스트 |
| MCP Synapse (API Key) | 9001 | MCP\_TEST\_PORT+1 | 인증 테스트 |
| MCP Synapse (OAuth) | 9002 | MCP\_TEST\_PORT+2 | OAuth 테스트 |
| A2A Echo Agent | **9003** | A2A\_ECHO\_PORT | A2A 기본 테스트 |
| A2A Math Agent | dynamic | (자동 할당) | A2A 수학 테스트 |
| Chaos MCP Server | 9999 | MCP\_CHAOS\_PORT | Chaos 테스트 |
| AgentHub API (E2E) | 8000 | E2E\_SERVER\_PORT | E2E Playwright Backend |
| Playground Static | 3000 | E2E\_STATIC\_PORT | E2E Playground Frontend |

**포트 충돌 방지:**

\# 환경변수로 포트 오버라이드  
MCP\_TEST\_PORT=8888 A2A\_ECHO\_PORT=8899 pytest \-n auto

## **🏷️ pytest Markers & Options**

### **Markers**

| 마커 | 설명 | 기본 동작 |
| :---- | :---- | :---- |
| @pytest.mark.llm | LLM API 호출 필요 (비용 발생) | **기본 제외** |
| @pytest.mark.local\_mcp | 로컬 MCP 서버 필요 (포트 9000\) | 기본 제외 |
| @pytest.mark.local\_a2a | 로컬 A2A 에이전트 필요 (포트 9003\) | 기본 제외 |
| @pytest.mark.e2e\_playwright | Full Browser E2E | **기본 제외** |
| @pytest.mark.chaos | Chaos Engineering 테스트 | 기본 제외 |
| @pytest.mark.integration | 통합 테스트 (명시적 마킹) | 기본 실행 |

### **기본 제외 마커 (pyproject.toml)**

\[tool.pytest.ini\_options\]  
addopts \= "-v \--tb=short \-m 'not llm and not e2e\_playwright and not local\_mcp and not local\_a2a and not chaos'"

### **커스텀 옵션**

| 옵션 | 설명 |
| :---- | :---- |
| \--run-llm | LLM 테스트 활성화 (API 키 \+ 비용 필요) |

## **🔄 Coverage Configuration**

### **설정 파일 우선순위**

1. **.coveragerc** (존재하면 최우선 \- 현재 프로젝트에서 사용)  
2. pyproject.toml \[tool.coverage.\*\] (fallback)

**현재 제외 설정:**

* src/domain/ports/\*\*/\*.py (인터페이스)  
* \*/\_\_init\_\_.py  
* src/main.py

## **⚡ Async Test Configuration (AnyIO Plugin)**

### **anyio\_mode \= "auto"**

**pyproject.toml:**

\[tool.pytest.ini\_options\]
anyio\_mode \= "auto"

**효과:**

* async def test\_\*() 형식의 테스트를 자동으로 비동기 테스트로 인식
* @pytest.mark.asyncio 데코레이터 불필요 (auto mode)
* anyio는 asyncio를 기본 backend로 사용하여 기존 asyncio API와 호환

**마이그레이션 배경:**

* pytest-asyncio는 fixture setup/teardown을 서로 다른 task에서 실행
* MCP SDK의 anyio.CancelScope는 동일 task 진입/탈출 요구
* anyio plugin은 fixture를 단일 task에서 실행하여 이 문제 해소

**관련 문서:** [ADR-T10: AnyIO Pytest Plugin Migration](../../docs/project/decisions/technical/ADR-T10-anyio-pytest-plugin-migration.md)

## **🌍 Environment Variables**

| 환경변수 | 기본값 | 설명 |
| :---- | :---- | :---- |
| MCP\_TEST\_PORT | 9000 | MCP 테스트 서버 포트 |
| E2E\_SERVER\_PORT | 8000 | E2E 백엔드 서버 포트 |
| E2E\_STATIC\_PORT | 3000 | E2E Playground Static 서버 포트 |
| SYNAPSE\_DIR | ~/Documents/GitHub/MCP\_SERVER/MCP\_Streamable\_HTTP | Synapse MCP 서버 경로 |

**Usage:**
```bash
# Port override
MCP_TEST_PORT=8888 pytest tests/integration

# Custom Synapse path
SYNAPSE_DIR=/custom/path pytest tests/integration
```

## **🧪 Playground JavaScript Tests**

**Location:** `tests/manual/playground/tests/`
**Framework:** Jest
**Command:**
```bash
cd tests/manual/playground
npm test
```

**Test files:**
- api-client.test.js (API 호출 모듈)
- sse-handler.test.js (SSE 스트리밍)
- ui-components.test.js (UI 렌더링)
- main.test.js (통합)