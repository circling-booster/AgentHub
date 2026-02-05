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
| AgentHub API (E2E) | 8000 | \- | E2E Playwright |

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

## **⚡ Async Test Configuration**

### **asyncio\_mode \= "auto"**

**pyproject.toml:**

\[tool.pytest.ini\_options\]  
asyncio\_mode \= "auto"

**효과:**

* async def test\_\*() 형식의 테스트를 자동으로 비동기 테스트로 인식  
* @pytest.mark.asyncio 데코레이터가 불필요해짐 (기존 코드 호환)