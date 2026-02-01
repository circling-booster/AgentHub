# Phase 8: 사용자 정의 도구 동적 로딩 (초안)

> **상태:** 📋 초안 (Phase 6C 완료 후 구체화)
> **선행 조건:** Phase 6 Part C (Plugin System) Complete
> **참조:** [ADR-0009](../decisions/0009-langgraph-a2a-not-plugin.md) - LangGraph는 A2A, Plugin은 개별 도구만

---



## 스케치

현재 EXTENSION 기능이 AGENTHUB 의 기능을 대부분 담지 못하고 있음.

### 추가할 기능

- 페이지 정보 전달


### 오류

- LLM 답변(MCP 서버 중 SYNAPSE - list dir 이용시) 시 화면이 사라지는 오류 - 크롬 콘솔 에러 확인
- agents 기능 확인 필요

## 범위 정의 (ADR-9 기반)

### 포함 (Plugin 대상)
- 사용자 정의 Python 함수 (.py 파일 업로드)
- LangChain 개별 Tool (WikipediaQueryRun, RequestsGet 등)
- REST API Wrapper
- `AGENTHUB_TOOLS` 컨벤션으로 도구 검출

### 제외 (A2A로 처리)
- LangGraph Agent (독립 프로세스 → A2A Agents 탭에서 URL 등록)
- CrewAI Agent (독립 프로세스 → A2A Agents 탭에서 URL 등록)
- 기타 에이전트 프레임워크 (A2A 프로토콜 사용)

---

## 핵심 아이디어

사용자가 .py 파일을 Extension에서 업로드하면, AgentHub가 `AGENTHUB_TOOLS` 변수를 검출하여 도구로 등록.

### 사용자 파일 형식

```python
# user_plugin.py
from langchain.tools import Tool

def my_custom_tool(query: str) -> str:
    return f"Result: {query}"

# AgentHub가 찾을 메타데이터
AGENTHUB_TOOLS = [
    Tool(
        name="MyTool",
        func=my_custom_tool,
        description="Custom tool"
    )
]
```

### 로딩 방식

```python
# 사용자 파일 동적 import
spec = importlib.util.spec_from_file_location("user_plugin", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# AGENTHUB_TOOLS 추출
tools = module.AGENTHUB_TOOLS
```

---

## 보안 고려사항

### 1. 실행 격리
| 옵션 | 설명 | 보안 수준 |
|------|------|:--------:|
| Docker 컨테이너 | 완전 격리 | 🟢 높음 |
| subprocess + 리소스 제한 | 프로세스 격리 | 🟡 중간 |
| RestrictedPython | AST 기반 제한 | 🟠 낮음 |

### 2. 의존성 관리

```yaml
# configs/allowed_dependencies.yaml
allowed:
  - langchain
  - requests
  - pandas
```

사용자 파일에서 허용 라이브러리만 import 가능. AgentHub가 미리 설치.

### 3. 검증 파이프라인
- 도구 schema 검사
- 악성 코드 스캔 (AST 분석)
- 샌드박스 테스트 실행

---

## Extension UI

```
Extension "Plugins" 탭:
  [+ Upload Plugin (.py)]
  ├─ File upload → Backend POST /api/plugins/upload
  ├─ 보안 검증 (AST 스캔)
  ├─ 샌드박스 테스트 실행
  ├─ 성공 시 등록
  └─ 도구 활성화
```

---

## 사용자 안내 (Extension Sidepanel)

```
┌─ 도구/에이전트 추가 가이드 ──────────────────┐
│                                               │
│ MCP 서버가 있나요?                            │
│   → "MCP Servers" 탭에서 URL 등록             │
│                                               │
│ LangGraph/CrewAI 에이전트가 있나요?           │
│   → "A2A Agents" 탭에서 URL 등록              │
│     (서버를 먼저 실행하세요)                    │
│                                               │
│ Python 함수를 도구로 추가하고 싶나요?         │
│   → "Plugins" 탭에서 .py 파일 업로드          │
│     (AGENTHUB_TOOLS 컨벤션 필요)              │
│                                               │
└───────────────────────────────────────────────┘
```

---

*초안 작성일: 2026-01-31*
*ADR-9 반영 수정일: 2026-02-01*
