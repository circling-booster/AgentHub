# AgentHub

Google ADK 기반 MCP + A2A 통합 Agent System

## Project Overview

| 항목 | 내용 |
|------|------|
| Language | Python 3.10+ |
| Architecture | Hexagonal (Ports and Adapters) |
| Agent Framework | Google ADK 1.23.0+ with LiteLLM |
| Default Model | `anthropic/claude-sonnet-4-20250514` |

**Core Flow:**
```
Chrome Extension → AgentHub API (localhost:8000) → MCP Servers / A2A Agents
```

## Directory Structure

```
src/
├── domain/           # Pure Python (no external dependencies)
│   ├── entities/     # Agent, Tool, Endpoint, Conversation
│   ├── services/     # OrchestratorService, ConversationService
│   └── ports/        # Port interfaces (inbound/outbound)
├── adapters/
│   ├── inbound/      # FastAPI HTTP, A2A Server
│   └── outbound/     # ADK, A2A Client, Storage (SQLite WAL)
└── config/           # DI container, pydantic-settings + YAML

extension/            # Chrome Extension (WXT + TypeScript)
├── entrypoints/      # background, offscreen, popup, sidepanel
└── lib/              # API client, SSE streaming
```

## How to Work

```bash
# Server
uvicorn src.main:app --host localhost --port 8000

# Extension dev
cd extension && npm run dev

# Tests
pytest
pytest --cov=src --cov-report=html
```

**Environment:** `.env` 파일에 `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` 설정

## Critical Constraints

| 제약 | 해결책 |
|------|--------|
| Service Worker 30s timeout | Offscreen Document 사용 |
| MCPToolset.get_tools() is async | Async Factory Pattern (FastAPI startup에서 초기화) |
| SQLite concurrent writes | WAL mode + write lock |
| Google Built-in Tools (SearchTool 등) | Gemini 전용 → MCP 서버로 대체 |

## Key Principles

- **IMPORTANT:** Domain layer는 순수 Python. 외부 라이브러리(ADK, FastAPI 등) import 금지
- **IMPORTANT:** MCP/A2A/ADK 구현 시 반드시 **Standards Verification Protocol** 준수
- Hexagonal Architecture: 도메인이 외부에 의존하지 않음. 어댑터가 도메인에 의존
- MCP Transport: Streamable HTTP 우선, SSE fallback (레거시 서버용)

## Standards Verification Protocol

MCP, A2A, ADK는 빠르게 진화하는 표준. **구현 전 웹 검색으로 최신 스펙 검증 필수.**

### 웹 검색 필수 시점

| 상황 | 확인 사항 |
|------|----------|
| 새 기능 구현 전 | API 메서드명, 파라미터, 반환 타입 |
| Import 에러 | 패키지 구조 변경, 모듈 리네이밍 |
| Deprecation Warning | 대체 API, 마이그레이션 가이드 |

### 표준별 확인 항목

| 표준 | 핵심 확인 |
|------|----------|
| **MCP** | Transport (Streamable HTTP/SSE), inputSchema 구조, Sampling 정책 |
| **A2A** | Agent Card 스펙, Handshake 프로토콜, JSON-RPC 2.0 |
| **ADK** | Import 경로 (`google.adk.*`), BaseToolset 인터페이스, Breaking Changes |

### 공식 소스 (우선순위)

| 표준 | 1순위 | 2순위 |
|------|-------|-------|
| **MCP** | [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification) | GitHub Issues |
| **A2A** | [google.github.io/adk-docs/a2a](https://google.github.io/adk-docs/a2a/) | Google Developers Blog |
| **ADK** | [google.github.io/adk-docs](https://google.github.io/adk-docs) | PyPI Changelog |

### Red Flags (즉시 재검증)

- `ImportError: cannot import name 'X'` → API 리네이밍/삭제
- `DeprecationWarning` → 대체 API 마이그레이션
- `TypeError: unexpected keyword argument` → 파라미터 변경

## Working Guidelines

- **한국어**로 소통 (별도 지시 없으면)
- 코드 패턴은 @docs/implementation-guide.md 참조

## Development Rules (자동화 강제 사항)

### 🚫 절대 금지

**main 브랜치에서 직접 Edit/Write 금지**
- PreToolUse Hook이 자동 차단 (exit 2)
- 항상 feature 브랜치에서 작업
- 확인 명령어: `git branch --show-current`

### ✅ 자동 실행 (사용자 개입 불필요)

**Stop Hook** (Claude 응답 완료 시 자동):
```bash
ruff check src/ tests/ --fix --quiet   # 린트 자동 수정 (src + tests)
ruff format src/ tests/ --quiet        # 포맷팅
pytest tests/ -q --tb=line             # 테스트 실행
```

**동작 방식:**
- Claude가 응답 완료 시 자동 트리거
- 실패해도 작업 차단 안됨 (exit 0 강제)
- 목적: 실시간 피드백, 코드 품질 유지
- 위치: `.claude/settings.json`

**중요:** Stop Hook의 pytest는 "경고용". 최종 품질 보장은 GitHub Actions CI에서 수행.

### 📋 PR 생성 전 수동 체크리스트

GitHub Actions가 자동 검증하지만, 로컬에서 미리 확인 권장:
- [ ] `pytest tests/ --cov=src --cov-report=term-missing`
- [ ] 커버리지 80% 이상
- [ ] `ruff check src/ tests/` 에러 없음
- [ ] feature 브랜치에서 작업 중

### 🤖 GitHub Actions 자동 검증

PR 생성 시 자동 실행 (`.github/workflows/ci.yml`):
- Python 3.10/3.11/3.12 매트릭스 테스트
- **`--cov-fail-under=80`** → 80% 미만 시 PR 차단
- ruff 린트/포맷 검사
- 타입 체크 (mypy)

### ⚠️ 주의사항

- Hook 에러 발생 시 `.claude/settings.json` 확인
- Hook 수정 후 Claude Code 재시작 필요 없음 (자동 반영)
- 자세한 흐름도: @docs/pre-implementation-review.md (라인 480-521)

### 🧪 테스트 린트 패턴

**`tests/`에서 `ARG` (미사용 인자) 규칙 비활성화** (`pyproject.toml`):
```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ARG"]
```

**이유:** Fake Adapter가 Port 인터페이스를 구현할 때 인자를 사용하지 않더라도 시그니처 유지 필요
```python
# 예시: Fake Orchestrator
async def process_message(self, message: str, conversation_id: str):
    # message, conversation_id는 인터페이스 준수를 위해 필요하나 미사용
    for chunk in self.responses:
        yield chunk
```

## User Context (ADHD/선택장애 지원)

프로젝트 오너는 ADHD 특성이 있으며 선택장애를 가지고 있음. 다음 상황에서 `decision-helper` 스킬 사용:

| 트리거 상황 | 예시 표현 |
|------------|----------|
| 모호한 상황 설명 | "뭘 해야 할지 모르겠어", "어떻게 해야 하지" |
| 여러 옵션 중 선택 필요 | "A랑 B 중에 뭐가 나을까" |
| 산만한 맥락 | 생각이 흩어져 있거나 두서없이 말할 때 |
| 결정 망설임 | "~해야 하나?", "~할까 말까" |

**핵심 원칙:**
- 선택지는 **최대 4개** (선택 마비 방지)
- **🔴🟡🟢** 긴급도 시각화
- 결정 문서는 `docs/decisions/YYYY-MM-DD-{주제}.md`에 기록
- 모든 결정에 **(추천)** 표시로 부담 감소

## Documentation

| 문서 | 내용 |
|------|------|
| @docs/roadmap.md | **구현 로드맵 v3.3** (Phase 0~4 세분화, 워크플로우 검증, Claude Code 연동) |
| @docs/architecture.md | 헥사고날 아키텍처 설계 |
| @docs/implementation-guide.md | 구현 패턴 및 코드 예시 (DynamicToolset, Async Factory, SQLite WAL, SSE, 보안 등) |
| @docs/extension-guide.md | Chrome Extension 개발 (Offscreen Document, Token Handshake 등) |
| @docs/risk-assessment.md | 리스크 평가 및 완화 전략 (보안, 동시성, Context Explosion 등) |
| @docs/decisions/ | Architecture Decision Records (ADR) - 주요 아키텍처 결정 기록 |
| @README.md | 빠른 시작, 설치, 기술 스택 |

## Test Resources

| Type | Resource |
|------|----------|
| MCP Test Server | `https://example-server.modelcontextprotocol.io/mcp` |
| A2A Samples | github.com/a2aproject/a2a-samples |

## Test Strategy (TDD + Hexagonal)

| Phase | 테스트 유형 | 대상 | 서브에이전트 | 커버리지 |
|-------|-----------|------|-------------|---------|
| Phase 1 | Unit | Domain Layer | tdd-agent | 80% |
| Phase 1.5 | Unit | Security Middleware | security-reviewer | - |
| Phase 2 | Integration | MCP Adapter, API | tdd-agent | 70% |
| Phase 2.5 | Integration | Extension ↔ Server | - | - |
| Phase 3 | E2E | Full Stack | code-reviewer | Critical Path |

**커스텀 서브에이전트:** `.claude/agents/`에 정의 (tdd-agent.md, security-reviewer.md, code-reviewer.md, hexagonal-architect.md)

**TDD 원칙:**
- Red-Green-Refactor 사이클 엄수
- Domain Layer는 Fake Adapter로 테스트 (외부 의존성 없이)
- 헥사고날 아키텍처 장점 활용: Port 인터페이스 기반 테스트 격리

**상세 계획:** @docs/roadmap.md 참조

## Subagent Workflow (명시적 호출 권장)

### 호출 시점

| Phase | 작업 | 서브에이전트 | 호출 방법 |
|-------|------|-------------|----------|
| **Phase 1** | Entity/Service 구현 전 | `tdd-agent` | "tdd-agent로 테스트 먼저 작성해줘" |
| **Phase 1** | Domain 코드 완료 후 | `hexagonal-architect` | "hexagonal-architect로 아키텍처 검토해줘" |
| **Phase 1.5** | 보안 코드 작성 후 | `security-reviewer` | "security-reviewer로 보안 검토해줘" |
| **Phase 2+** | 기능 완료/PR 전 | `code-reviewer` | "code-reviewer로 코드 리뷰해줘" |


### 워크플로우 예시

```
[Phase 1 시작]
사용자: "Endpoint 엔티티를 구현해줘"
Claude: "tdd-agent로 테스트를 먼저 작성하는 게 좋을까요?" (제안 가능)
사용자: "네" 또는 "tdd-agent로 테스트 작성해줘" (명시적 요청)

[구현 완료]
사용자: "code-reviewer로 리뷰해줘"
Claude: [code-reviewer 호출하여 아키텍처/품질 검토]
```

### Phase별 상세 호출 시점

자세한 시점과 예시는 @docs/roadmap.md의 각 Phase 섹션 참조
