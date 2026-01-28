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
- **IMPORTANT:** MCP/A2A/ADK 구현 시 반드시 웹 검색으로 최신 API 확인 (표준이 빠르게 변화)
- Hexagonal Architecture: 도메인이 외부에 의존하지 않음. 어댑터가 도메인에 의존
- MCP Transport: Streamable HTTP 우선, SSE fallback (레거시 서버용)

## Working Guidelines

- **한국어**로 소통 (별도 지시 없으면)
- 기능 구현 전 공식 문서 확인 필수
- 코드 패턴은 @docs/implementation-guide.md 참조

## Documentation

| 문서 | 내용 |
|------|------|
| @docs/architecture.md | 헥사고날 아키텍처 설계 |
| @docs/implementation-guide.md | 구현 패턴 및 코드 예시 (DynamicToolset, Async Factory, SQLite WAL, SSE, 보안 등) |
| @docs/extension-guide.md | Chrome Extension 개발 (Offscreen Document, Token Handshake 등) |
| @docs/risk-assessment.md | 리스크 평가 및 완화 전략 (보안, 동시성, Context Explosion 등) |
| @README.md | 빠른 시작, 설치, 기술 스택 |

## Test Resources

| Type | Resource |
|------|----------|
| MCP Test Server | `https://example-server.modelcontextprotocol.io/mcp` |
| A2A Samples | github.com/a2aproject/a2a-samples |
