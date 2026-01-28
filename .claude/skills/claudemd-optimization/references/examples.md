# CLAUDE.md 변환 예시

## 목차

1. [Before/After 비교](#beforeafter-비교)
2. [최적화된 CLAUDE.md 템플릿](#최적화된-claudemd-템플릿)

---

## Before/After 비교

### Before (982줄)

```markdown
## Commands and Agents Available
### Frontend Plugin
**Agents:**
- `typescript-frontend-dev` - TypeScript/React implementation (Sonnet)
- `frontend-architect` - Architecture planning (Sonnet)
- `ui-designer` - UI/UX design specialist (Sonnet)
[... 100+ lines of agent details ...]

## Claudemem AST Structural Analysis (v0.3.0)
### Installation
npm install -g claudemem
### Usage
claudemem analyze ./src
### Configuration
[... 150+ lines of tool documentation ...]

## Parallel Multi-Model Execution Protocol
### Overview
This protocol enables...
### Configuration
[... 180+ lines of protocol details ...]

## Code Style Guidelines
- Use 2-space indentation
- Prefer const over let
- Always use semicolons
[... 50+ lines of style rules ...]
```

### After (127줄)

```markdown
# Project Name

## Project Overview
TypeScript monorepo with React frontend and Node.js backend.
Primary purpose: Agent orchestration system.

## Directory Structure
src/
├── domain/       # Business logic
├── adapters/     # External integrations
└── config/       # Configuration

## How to Work
- Build: `bun build`
- Test: `bun test`
- Lint: `bun lint` (auto-fixes style)

## Key Principles
- Hexagonal Architecture
- Dependency Injection
- Domain-Driven Design

## Documentation

See @README.md for project overview.
See @docs/architecture.md for detailed architecture.

| Topic | Reference |
|-------|-----------|
| Commands & Agents | @docs/commands-and-agents.md |
| Claudemem Guide | @docs/claudemem-guide.md |
| Parallel Execution | @docs/parallel-execution-protocol.md |

## Project Rules

IMPORTANT: Communicate in Korean unless specified otherwise.
YOU MUST use web search for MCP/A2A/ADK info (standards evolve rapidly).
ALWAYS verify API patterns before implementation.
```

### 변환 요약

| 항목 | Before | After |
|------|--------|-------|
| 총 라인 | 982 | 127 |
| 에이전트 목록 | 100줄 인라인 | docs/ 참조 |
| 도구 문서 | 150줄 인라인 | docs/ 참조 |
| 프로토콜 | 180줄 인라인 | docs/ 참조 |
| 스타일 규칙 | 50줄 | 삭제 (린터 사용) |

---

## 최적화된 CLAUDE.md 템플릿

```markdown
# {프로젝트명}

## Project Overview
{1-3문장: 프로젝트 목적과 기술 스택}

## Directory Structure
{src/ 기준 10-15줄 트리}

## How to Work

### Setup
{환경 설정 2-3줄}

### Commands
| 작업 | 명령어 |
|------|--------|
| Build | `{build command}` |
| Test | `{test command}` |
| Lint | `{lint command}` |

### Environment Variables
| 변수 | 용도 |
|------|------|
| `{VAR}` | {설명} |

## Key Principles
- {원칙 1}
- {원칙 2}
- {원칙 3}

## Important Files

| 역할 | 파일 |
|------|------|
| 진입점 | `src/main.py` |
| 설정 | `src/config/settings.py` |

## Documentation

See @README.md for project overview.

| 주제 | 참조 |
|------|------|
| {주제1} | @docs/{file1}.md |
| {주제2} | @docs/{file2}.md |

## Project Rules

IMPORTANT: {핵심 규칙 - 반드시 준수}
- {규칙 1: 모든 작업에 적용}
- {규칙 2: 모든 작업에 적용}
```

### 템플릿 사용 시 주의

1. `{}` 부분만 프로젝트에 맞게 채움
2. 불필요한 섹션은 삭제
3. 60-150줄 유지
4. 작업별 세부사항은 docs/로 분리
