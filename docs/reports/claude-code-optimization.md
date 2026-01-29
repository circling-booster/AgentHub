# AgentHub - Claude Code 최적화 분석

> Skills, Hooks, Agents 현황 분석 및 2026 베스트 프랙티스 기반 권장사항

**작성일:** 2026-01-29
**기준:** Claude Code 2.0 (2026년 1월 최신 기능)

---

## 1. 현재 구성 평가

### ✅ 잘 구성된 항목

| 항목 | 현재 설정 | 평가 |
|------|----------|------|
| **TDD Agent** | Isolated subagent, Red-Green-Refactor 강제 | ⭐⭐⭐⭐⭐ 최신 베스트 프랙티스 완벽 준수 |
| **Workflow Plugins** | `tdd-workflows`, `full-stack-orchestration` | ⭐⭐⭐⭐ 공식 플러그인 활용 우수 |
| **Stop Hook** | ruff + pytest 자동 실행 | ⭐⭐⭐⭐ 효율적인 품질 검증 |
| **Custom Agents** | 5개 전문 에이전트 (TDD, Security, Code Review, Hexagonal, ADR) | ⭐⭐⭐⭐ 프로젝트 맞춤형 구성 |

### ⚠️ 개선 필요 항목

| 항목 | 현재 설정 | 문제점 | 권장 변경 |
|------|----------|--------|----------|
| **PreToolUse Hook** | main 브랜치 Edit/Write 차단 | Write-time blocking은 2026 베스트 프랙티스 위반 | SessionEnd 또는 UserPromptSubmit으로 변경 |
| **Skills** | 미사용 | Auto-invoked 컨텍스트 로딩 기회 상실 | 프로젝트별 Skills 추가 |
| **pytest in Stop Hook** | 응답 완료 후 실행 | 실패 시 수정 후 재실행 필요 | PostToolUse로 이동 고려 |

---

## 2. 2026년 베스트 프랙티스 기반 권장사항

### 🚫 비권장: PreToolUse Hook의 Write-time Blocking

**문제점:**
```json
// ❌ 현재 설정 (비권장)
"PreToolUse": [{
  "matcher": "Edit|Write",
  "hooks": [{"command": "...check main branch..."}]
}]
```

**2026년 연구 결과:**
> "Use hooks to enforce state validation at commit time (block-at-submit). **Avoid blocking at write time**—let the agent finish its plan, then check the final result."
> — [Claude Code Hooks Best Practices (2026)](https://www.eesel.ai/blog/hooks-in-claude-code)

**이유:**
1. **컨텍스트 낭비:** 매 Edit/Write마다 실행 → 응답마다 수십 번 실행
2. **워크플로우 방해:** 에이전트의 계획 수립 단계에서 중단
3. **False Positive:** 임시 파일 수정도 차단

**권장 대안:**
```json
// ✅ 권장: SessionEnd 또는 git commit hook 사용
"SessionEnd": [{
  "hooks": [{
    "type": "command",
    "command": "git rev-parse --abbrev-ref HEAD | grep -qx main && echo 'Session on main branch - review commits before push' || exit 0"
  }]
}]
```

---

### ✅ 권장: TDD Agent의 Isolated Context

**현재 구성 (우수):**
```yaml
---
name: tdd-agent
description: Expert TDD orchestrator for AgentHub project...
model: sonnet
---
```

**2026년 TDD 연구 결과:**
> "When everything runs in one context window, the LLM cannot truly follow TDD - this fundamentally breaks TDD because the whole point of writing the test first is that you don't know the implementation yet. **This is why subagents with isolated contexts are crucial for proper TDD.**"
> — [Forcing Claude Code to TDD (2026)](https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/)

**AgentHub가 잘하고 있는 점:**
- ✅ Subagent로 분리되어 isolated context 확보
- ✅ Red-Green-Refactor 사이클 명시적 정의
- ✅ Fake Adapter 패턴으로 헥사고날 아키텍처 TDD 구현

**추가 개선 제안:**
```yaml
# tdd-agent.md 개선
---
name: tdd-agent
description: Expert TDD orchestrator for AgentHub project...
model: sonnet
tools: [Read, Write, Bash]  # ← 도구 제한으로 focus 강화
---
```

---

### 🎯 권장: Skills 추가 활용

**Skills vs Agents 차이:**

| 특성 | Skills | Agents |
|------|--------|--------|
| **실행 방식** | Auto-invoked (description matching) | 명시적 호출 필요 |
| **컨텍스트** | On-demand 로딩 | 항상 메모리 점유 |
| **용도** | 반복 지침, 코드 패턴 | 복잡한 워크플로우 |

**AgentHub에 권장 Skills:**

#### 1. **Hexagonal Architecture Pattern Skill**
```yaml
# .claude/skills/hexagonal-patterns.md
---
name: hexagonal-patterns
description: AgentHub hexagonal architecture code patterns and conventions
tags: [architecture, domain, adapter, ports]
---

## Domain Layer Patterns

**순수성 원칙:**
```python
# ✅ Domain Layer
from domain.ports.outbound.storage_port import StoragePort

# ❌ Domain Layer에서 금지
from fastapi import FastAPI  # 외부 라이브러리
```

## Port Interface Pattern
[... implementation-guide.md에서 자동 로딩 ...]
```

**효과:**
- 대화 중 "domain layer" 언급 시 자동 로딩
- 에이전트가 아키텍처 원칙을 항상 참조
- 컨텍스트 윈도우 절약 (on-demand)

#### 2. **Security Checklist Skill**
```yaml
# .claude/skills/security-checklist.md
---
name: security-checklist
description: Security validation for localhost API and Chrome Extension
tags: [security, cors, token, rce]
---

## Localhost API Security

**Token Handshake 검증:**
- [ ] X-Extension-Token 헤더 검증
- [ ] CORS Origin 제한 (chrome-extension://*)
- [ ] Session Storage 사용 (Local Storage 금지)
[...]
```

**효과:**
- 보안 관련 코드 작성 시 자동 로딩
- 수동 에이전트 호출 불필요

---

### 📊 권장: Hook 전략 재구성

**현재 문제:**
```json
"Stop": [{
  "command": "ruff check src/ tests/ --fix --quiet; ruff format src/ tests/ --quiet; pytest tests/ -q --tb=line || true"
}]
```

**문제점:**
1. **pytest 실행 타이밍:** Stop Hook은 응답 완료 후 실행 → 실패 시 다시 요청 필요
2. **에러 무시:** `|| true`로 실패를 숨김

**2026년 권장 전략:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "ruff check src/ tests/ --fix --quiet 2>/dev/null && ruff format src/ tests/ --quiet 2>/dev/null"
        }]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "pytest tests/unit/ -q --tb=line --maxfail=1 2>&1 | head -20 || echo 'Tests failed - review before commit'"
        }]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "commit|pr|push",
        "hooks": [{
          "type": "command",
          "command": "pytest tests/ --cov=src --cov-fail-under=80 -q"
        }]
      }
    ]
  }
}
```

**변경 이유:**

| Hook | 변경 사항 | 효과 |
|------|----------|------|
| **PostToolUse** | ruff만 실행 (pytest 제거) | 코드 작성 즉시 포맷팅, 빠른 피드백 |
| **Stop** | pytest unit만 실행, 실패 메시지 표시 | 간단한 테스트로 빠른 검증 |
| **UserPromptSubmit** | commit 키워드 시 전체 테스트 + 커버리지 | 품질 보장, 시기 적절한 검증 |

**참고:** [DataCamp - Claude Code Hooks (2026)](https://www.datacamp.com/tutorial/claude-code-hooks)

---

## 3. 추가 권장 구성

### 🆕 신규 Skill: MCP/ADK Standards Verification

```yaml
# .claude/skills/mcp-adk-standards.md
---
name: mcp-adk-standards
description: Latest MCP and Google ADK API verification patterns (2026)
tags: [mcp, adk, api, standards]
---

## MCP Transport (2026 Spec)

**권장:** Streamable HTTP
**폴백:** SSE (레거시 서버)

```python
# DynamicToolset._create_mcp_toolset()
try:
    toolset = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(url=url, timeout=120)
    )
    await toolset.get_tools()  # 연결 테스트
    return toolset
except Exception:
    # SSE 폴백
    toolset = MCPToolset(
        connection_params=SseServerParams(url=url, timeout=120)
    )
```

**웹 검색 필수 시점:**
- [ ] Plan 단계: 아키텍처 영향 확인
- [ ] 구현 단계: API 시그니처 재검증
- [ ] Import 에러: 패키지 구조 변경 확인

**출처:** @docs/standards-verification.md
```

**효과:**
- MCP/ADK 관련 코드 작성 시 자동으로 최신 스펙 가이드 로딩
- 웹 검색 타이밍 자동 리마인드

---

### 🆕 신규 Agent: Phase Orchestrator

```yaml
# .claude/agents/phase-orchestrator.md
---
name: phase-orchestrator
description: AgentHub roadmap phase management - enforce phase boundaries and DoD validation
model: sonnet
---

You are the **Phase Orchestrator** for AgentHub project.

## 역할

각 Phase의 DoD (Definition of Done) 검증 및 단계별 품질 보장.

## Phase 상태 (2026-01-29)

| Phase | 상태 | DoD 문서 |
|-------|------|----------|
| Phase 0 | ✅ 완료 | roadmap.md |
| Phase 1 | ✅ 완료 | plans/phase1.0.md |
| Phase 1.5 | ✅ 완료 | plans/phase1.5.md |
| Phase 2 | 📋 예정 | plans/phase2.0.md |

## DoD 체크리스트

### Phase 2 시작 전 검증:
- [ ] Phase 1.5 모든 DoD 항목 완료
- [ ] 테스트 커버리지 80% 이상
- [ ] 문서 업데이트 (src/README.md 보안 섹션)

### Phase 진행 중:
- [ ] 각 단계별 테스트 작성 (TDD)
- [ ] 아키텍처 원칙 준수 검증
- [ ] 보안 체크리스트 확인

## 명령어

사용자가 "다음 phase", "phase 2 시작" 등 요청 시:
1. 현재 Phase DoD 검증
2. 미완료 항목 리스트 제공
3. 다음 Phase 시작 조건 확인
```

**사용 시점:**
- Phase 전환 시 DoD 자동 검증
- Roadmap 준수 보장

---

## 4. 최종 권장 구성

### 📋 .claude/settings.json (최적화)

```json
{
  "enabledPlugins": {
    "tdd-workflows@claude-code-workflows": true,
    "full-stack-orchestration@claude-code-workflows": true
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "ruff check src/ tests/ --fix --quiet 2>/dev/null; ruff format src/ tests/ --quiet 2>/dev/null"
        }]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "pytest tests/unit/ -q --tb=line --maxfail=1 2>&1 | head -20 || echo '⚠️  Unit tests failed - review before commit'"
        }]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "commit|pr|push",
        "hooks": [{
          "type": "command",
          "command": "pytest tests/ --cov=src --cov-fail-under=80 -q || (echo '❌ Coverage below 80%' && exit 1)"
        }]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [{
          "type": "command",
          "command": "git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -qx main && echo '⚠️  Session ended on main branch - ensure commits are reviewed' || exit 0"
        }]
      }
    ]
  }
}
```

### 📋 필수 Skills (신규 생성)

| Skill | 파일명 | 용도 | 우선순위 |
|-------|--------|------|:-------:|
| Hexagonal Patterns | `hexagonal-patterns.md` | 아키텍처 패턴 자동 로딩 | 🔴 높음 |
| Security Checklist | `security-checklist.md` | 보안 검증 자동화 | 🔴 높음 |
| MCP/ADK Standards | `mcp-adk-standards.md` | API 스펙 검증 | 🟡 중간 |
| Git Workflow | `git-workflow.md` | 브랜치 전략, PR 템플릿 | 🟢 낮음 |

### 📋 Agents 유지/추가

| Agent | 현재 상태 | 조치 |
|-------|----------|------|
| tdd-agent | ✅ 우수 | **유지** - isolated context 완벽 구현 |
| security-reviewer | ✅ 양호 | **유지** - Phase 1.5+ 필수 |
| code-reviewer | ✅ 양호 | **유지** |
| hexagonal-architect | ✅ 양호 | **유지** |
| adr-specialist | ✅ 양호 | **유지** |
| **phase-orchestrator** | ❌ 미생성 | **신규 추가** - DoD 검증 자동화 |

---

## 5. 마이그레이션 체크리스트

### 즉시 적용 (High Priority)

- [ ] **PreToolUse Hook 제거** → SessionEnd로 대체
- [ ] **PostToolUse Hook 추가** (ruff 자동 포맷팅)
- [ ] **UserPromptSubmit Hook 추가** (commit 전 전체 테스트)
- [ ] **hexagonal-patterns.md Skill 생성**
- [ ] **security-checklist.md Skill 생성**

### Phase 2 시작 전 (Medium Priority)

- [ ] **mcp-adk-standards.md Skill 생성**
- [ ] **phase-orchestrator.md Agent 생성**
- [ ] **Stop Hook 개선** (pytest 결과 가독성)

### 선택적 (Low Priority)

- [ ] **git-workflow.md Skill 생성**
- [ ] **tdd-agent.md에 tools 제한 추가**

---

## 6. 참고 자료

### 공식 문서
### 2026년 베스트 프랙티스

### 커뮤니티 리소스


---

## 7. 요약

### ✅ AgentHub가 잘하고 있는 것

1. **TDD Agent 구조** - Isolated context로 진정한 TDD 구현
2. **Workflow Plugins** - 공식 플러그인 활용
3. **Custom Agents** - 프로젝트 맞춤형 전문 에이전트
4. **Stop Hook** - 자동 품질 검증

### ⚠️ 개선이 필요한 것

1. **PreToolUse Hook** - Write-time blocking 제거 필요
2. **Skills 미활용** - Auto-invoked 컨텍스트 로딩 기회 상실
3. **pytest 타이밍** - Stop보다 UserPromptSubmit이 적절

### 🎯 추가하면 좋은 것

1. **PostToolUse Hook** - 코드 작성 즉시 포맷팅
2. **Hexagonal Patterns Skill** - 아키텍처 패턴 자동 로딩
3. **Security Checklist Skill** - 보안 검증 자동화
4. **Phase Orchestrator Agent** - DoD 검증 자동화

---

*문서 생성일: 2026-01-29*
*기준: Claude Code 2.0 (2026년 1월)*
