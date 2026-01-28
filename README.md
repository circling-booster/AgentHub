# AgentHub

> Google ADK 기반 MCP + A2A 통합 Agent System

**AgentHub**는 개발자와 파워유저가 **다양한 AI 도구(MCP)와 에이전트(A2A)를** 로컬 환경에서 통합 관리하고, **Chrome Extension으로 브라우저에서 바로 호출**할 수 있게 해주는 데스크톱 애플리케이션입니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **Chrome Extension** | 웹 페이지에서 직접 LLM과 대화 및 도구 호출 |
| **동적 등록** | UI에서 MCP 서버 / A2A 에이전트 URL 추가/제거 (재시작 불필요) |
| **다중 LLM 지원** | Claude, GPT-4, Gemini 등 100+ LLM 지원 (LiteLLM) |
| **MCP + A2A 통합** | 도구(MCP)와 에이전트(A2A) 프로토콜 네이티브 지원 |

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────┐
│                  Chrome Extension                    │
│            (Manifest V3 + Offscreen Document)        │
└──────────────────────────┬──────────────────────────┘
                           ↓ HTTP REST + SSE
┌─────────────────────────────────────────────────────┐
│              AgentHub API Server (ADK)              │
│                                                     │
│   LlmAgent (LiteLLM) + DynamicToolset (MCP)        │
└──────────────────────────┬──────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌───────────────┐                    ┌───────────────┐
│  MCP Servers  │                    │  A2A Agents   │
│  (외부 도구)   │                    │  (외부 에이전트)│
└───────────────┘                    └───────────────┘
```

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| **Agent Framework** | Google ADK 1.23.0+ |
| **LLM Integration** | LiteLLM (100+ LLM) |
| **API Server** | FastAPI |
| **Extension** | WXT + TypeScript |
| **Database** | SQLite (WAL mode) |
| **MCP Transport** | Streamable HTTP |

---

## 빠른 시작

### 요구사항

- Python 3.10+
- Node.js 18+

### 설치

```bash
# 저장소 클론
git clone https://github.com/user/agenthub.git
cd agenthub

# Python 가상환경
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Extension 의존성
cd extension && npm install
```

### 환경변수

```bash
# .env 파일 생성
cp .env.example .env

# API 키 설정 (사용하려는 LLM)
ANTHROPIC_API_KEY=your-api-key
OPENAI_API_KEY=your-api-key
GOOGLE_API_KEY=your-api-key
```

### 실행

```bash
# API 서버
uvicorn src.main:app --host localhost --port 8000

# Extension 개발 모드 (별도 터미널)
cd extension && npm run dev
```

---

## 문서

| 문서 | 설명 |
|------|------|
| [docs/architecture.md](docs/architecture.md) | 헥사고날 아키텍처 설계 |
| [docs/implementation-guide.md](docs/implementation-guide.md) | 구현 패턴 및 코드 예시 |
| [docs/extension-guide.md](docs/extension-guide.md) | Chrome Extension 개발 가이드 |
| [docs/feasibility-analysis-2026-01.md](docs/feasibility-analysis-2026-01.md) | 기술 스택 분석 |

---

## 디렉토리 구조

```
agenthub/
├── src/                    # Python 백엔드 (Hexagonal Architecture)
│   ├── domain/             # 도메인 로직 (순수 Python)
│   ├── adapters/           # 어댑터 (FastAPI, ADK, Storage)
│   └── config/             # 설정 (pydantic-settings, DI)
│
├── extension/              # Chrome Extension (WXT + TypeScript)
│   ├── entrypoints/        # 엔트리포인트 (popup, sidepanel, background, offscreen)
│   └── lib/                # 유틸리티 (API, SSE 클라이언트)
│
├── configs/                # YAML 설정 파일
├── docs/                   # 상세 문서
└── tests/                  # 테스트
```

---

## 테스트

```bash
# 전체 테스트
pytest

# 커버리지 리포트
pytest --cov=src --cov-report=html
```

---

## 참고 자료

### 공식 문서
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [A2A Protocol](https://a2a-protocol.org/)
- [WXT Framework](https://wxt.dev/)

### 개발 도구
- [LiteLLM](https://docs.litellm.ai/)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [dependency-injector](https://python-dependency-injector.ets-labs.org/)

---

## 라이선스

[Apache 2.0](LICENSE)
