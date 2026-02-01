# AgentHub Skill & Agent 활용 가이드

> Phase별 최적 Skill/Agent 호출 전략 및 워크플로우 가이드

**작성일:** 2026-01-29
**대상:** AgentHub 프로젝트 개발자

---

## 목차

1. [사용 가능한 도구 현황](#사용-가능한-도구-현황)
2. [Phase별 활용 전략](#phase별-활용-전략)
3. [선택적 활용 (상황별)](#선택적-활용-상황별)
4. [자동 트리거 설정](#자동-트리거-설정)
5. [핵심 원칙](#핵심-원칙)

---

## 사용 가능한 도구 현황

### Skills (Skill tool 호출)

| Skill | 목적 | 주요 사용 시점 |
|-------|------|---------------|
| **hexagonal-patterns** | 헥사고날 아키텍처 패턴 검증 | Domain/Adapter 구현 시 |
| **mcp-adk-standards** | ADK/MCP API 최신 스펙 검증 | MCP 코드 작성 전 (Plan & 구현 양쪽) |
| **security-checklist** | 보안 리뷰 체크리스트 실행 | 보안 관련 코드 작성 후 |
| **tdd** | TDD Red-Green-Refactor 워크플로우 | Entity/Service 구현 전 |
| code-explainer | 코드 분석 및 문서화 | 복잡한 로직 이해 필요 시 |
| decision-helper | 의사결정 구조화 도구 | 기술 선택 고민 시 |
| claudemd-optimization | CLAUDE.md 최적화 | 문서가 200줄 초과 시 |

### Agents (Task tool 호출)

| Agent | 목적 | 주요 사용 시점 |
|-------|------|---------------|
| **tdd-agent** | TDD 사이클 강제 및 테스트 작성 | 구현 전 자동 호출 |
| **hexagonal-architect** | 헥사고날 아키텍처 검증 | 레이어 설계 시 |
| **security-reviewer** | 보안 취약점 감사 | 보안 코드 작성 후 |
| **code-reviewer** | 코드 품질 및 아키텍처 리뷰 | 기능 완료 후, PR 전 |
| **adr-specialist** | Architecture Decision Records 생성 | 아키텍처 의사결정 시 |
| **phase-orchestrator** | Phase DoD 검증 | Phase 완료 시 |
| Explore | 코드베이스 구조 탐색 | 전체 구조 파악 필요 시 |
| Plan | 구현 계획 수립 | 복잡한 기능 시작 전 |

---

## Phase별 활용 전략

### Phase 2: MCP Integration (현재 예정)

#### 2.1 구현 전 (Planning)

##### 📋 Standards Verification (필수)

```markdown
Skill: mcp-adk-standards
호출: /mcp-adk-standards

사용 시점: ADK/MCP 코드 작성 **전**

이유:
- MCP/ADK는 빠르게 진화하는 표준
- Plan 단계와 구현 단계 **양쪽 모두** 웹 검색 필수
- Import 경로, API 시그니처, Breaking Changes 재검증

예시:
"DynamicToolset 구현 전 MCPToolset.get_tools() API 최신 스펙 확인"
"google.adk.tools.mcp_tool import 경로 2026년 검증"
```

##### 🏗️ Architecture Review

```markdown
Agent: hexagonal-architect
호출: Task tool with subagent_type="hexagonal-architect"

사용 시점: DynamicToolset, AdkOrchestratorAdapter 설계 시

이유:
- ADK Adapter가 Domain에 올바르게 의존성 주입하는지 검증
- BaseToolset 상속이 Outbound Port 패턴과 부합하는지 확인
- Domain Layer에 외부 라이브러리 import 혼입 방지

예시:
"DynamicToolset이 domain/ports/outbound/toolset_port를 구현하는지 검토"
```

##### 🗺️ Implementation Planning

```markdown
Agent: Plan
호출: EnterPlanMode tool

사용 시점: 복잡한 기능(DynamicToolset, SSE Streaming) 시작 전

이유:
- 비동기 초기화 패턴(Async Factory) 설계 필요
- Streamable HTTP vs SSE 폴백 로직 계획
- Zombie Task 방지 전략 수립
- Context Explosion 완화 설계

예시:
"DynamicToolset의 Async Factory Pattern 적용 전 설계 검토 필요"
```

#### 2.2 구현 중 (Development)

##### 🧪 TDD Workflow (자동 트리거)

```markdown
Skill: tdd
호출: /tdd (또는 자동 감지)

사용 시점: Entity/Service/Adapter 구현 **전**

이유:
- Red-Green-Refactor 사이클 강제
- DynamicToolset은 Fake Adapter 테스트 가능
- Domain 순수성 보장
- 테스트 커버리지 80% 목표 달성

자동 트리거:
"Implement DynamicToolset" 입력 시
"Create AdkOrchestratorAdapter" 입력 시
```

##### 🏗️ Hexagonal Pattern Validation

```markdown
Skill: hexagonal-patterns
호출: /hexagonal-patterns

사용 시점: Adapter 구현 중

이유:
- Domain Layer에 ADK, FastAPI import 혼입 방지
- Port 인터페이스 기반 DI 패턴 검증
- Fake Adapter 테스트 작성 가이드
- Dependency 방향 확인 (Adapter → Domain)

예시:
"AdkOrchestratorAdapter 구현 시 호출"
"DynamicToolset이 BaseToolset과 ToolsetPort 모두 준수하는지 검증"
```

#### 2.3 구현 후 (Review)

##### 🔐 Security Review

```markdown
Agent: security-reviewer
호출: Task tool with subagent_type="security-reviewer"

사용 시점: API 엔드포인트 구현 후

이유:
- Token Handshake 검증
- CORS 설정 확인
- Input Validation 체크
- SSE 엔드포인트 보안 검토

예시:
"POST /api/mcp/servers 구현 완료 후 보안 검토"
"POST /api/chat/stream SSE 엔드포인트 보안 검토"
```

##### 📝 ADR Documentation

```markdown
Agent: adr-specialist
호출: Task tool with subagent_type="adr-specialist"

사용 시점: 중요한 아키텍처 결정 시

이유:
- Transport Protocol 선택(Streamable HTTP vs SSE) 기록
- Context Explosion 완화 전략 문서화
- 트레이드오프 명시적 기록

예시:
"MCP Transport로 Streamable HTTP 우선 선택 결정 후 ADR 생성"
"MAX_ACTIVE_TOOLS=30 제한 정책 결정 후 ADR 생성"
```

##### ✅ Code Quality Review

```markdown
Agent: code-reviewer
호출: Task tool with subagent_type="code-reviewer"

사용 시점: Phase 2 기능 완료 후, PR 전

이유:
- 헥사고날 아키텍처 준수 검증
- ADK/MCP 패턴 일관성 확인
- 테스트 커버리지 검토 (70% 이상)
- 코드 품질 최종 점검

자동 트리거:
"Phase 2 완료, 코드 리뷰 필요" 입력 시
```

#### 2.4 Phase 완료 시

##### 🏁 Phase DoD Verification

```markdown
Agent: phase-orchestrator
호출: Task tool with subagent_type="phase-orchestrator"

사용 시점: Phase 2 모든 작업 완료 후

이유:
- DoD 체크리스트 자동 검증
- 테스트 커버리지 70% 확인
- 문서화 완성도 검토 (src/adapters/README.md 생성 확인)
- 다음 Phase 이행 가능 여부 판정

예시:
"Phase 2 MCP Integration 완료, DoD 검증 요청"

검증 항목:
- [ ] MCP 테스트 서버 연결 성공
- [ ] 도구 목록 조회 API 동작
- [ ] 도구 개수 30개 초과 시 에러 반환
- [ ] SSE 스트리밍 응답 정상 동작
- [ ] 통합 테스트 커버리지 70% 이상
- [ ] src/adapters/README.md 생성
- [ ] src/README.md MCP 아키텍처 섹션 추가
```

---

### Phase 2.5: Chrome Extension

#### 2.5.1 구현 전 (Planning)

##### 🔍 Standards Verification

```markdown
Skill: mcp-adk-standards
호출: /mcp-adk-standards

사용 시점: Offscreen Document 설계 전

이유:
- Chrome Extension Manifest V3 최신 스펙 확인
- Offscreen Document API 변경사항 검증
- Service Worker Lifecycle 2026년 업데이트 확인

예시:
"chrome.offscreen.createDocument API 사용 전 2026년 스펙 확인"
"Service Worker 30초 타임아웃 정책 변경 여부 검증"
```

##### 🔐 Security Architecture Review

```markdown
Skill: security-checklist
호출: /security-checklist

사용 시점: Token Handshake 클라이언트 설계 시

이유:
- Extension ↔ Server 보안 패턴 검증
- Drive-by RCE 방지 전략 확인
- CORS, Origin 검증 체크
- chrome.storage.session 보안 검토

예시:
"Extension 보안 설계 전 체크리스트 실행"
"Token 저장 방식(session vs local) 보안 검토"
```

#### 2.5.2 구현 중 (Development)

##### 🧪 TDD for Client Code

```markdown
Skill: tdd
호출: /tdd

사용 시점: SSE Client, API Client 구현 전

이유:
- fetch ReadableStream 로직 테스트
- Reconnection 로직 검증
- Error Handling 테스트

예시:
"SSE Client streamChat() 구현 전 TDD 시작"
"authenticatedFetch() 구현 전 테스트 작성"
```

#### 2.5.3 구현 후 (Review)

##### 🔐 Security Review

```markdown
Agent: security-reviewer
호출: Task tool with subagent_type="security-reviewer"

사용 시점: Token Handshake 구현 후

이유:
- chrome.storage.session 사용 적절성 검증
- Token 누출 위험 점검
- X-Extension-Token 헤더 주입 로직 검증
- Origin 검증 로직 확인

예시:
"Extension 인증 로직 완료, 보안 검토"
"background.ts initializeAuth() 구현 후 보안 검토"
```

##### 🏁 Phase DoD Verification

```markdown
Agent: phase-orchestrator
호출: Task tool with subagent_type="phase-orchestrator"

사용 시점: Phase 2.5 완료 후

검증 항목:
- [ ] Extension 설치 시 서버와 자동 토큰 교환 성공
- [ ] Sidepanel에서 "Hello" 입력 시 Claude 응답
- [ ] MCP 도구 호출 결과가 UI에 표시
- [ ] 브라우저 종료 후 재시작 시 토큰 재발급 정상 동작
- [ ] extension/README.md 생성
- [ ] 루트 README.md에 Extension 사용법 추가
```

---

### Phase 3: Stability & A2A Integration

#### 3.1 구현 전 (Planning)

##### 🔍 A2A Standards Verification

```markdown
Skill: mcp-adk-standards
호출: /mcp-adk-standards

사용 시점: A2A Agent Card 구현 전

이유:
- A2A 프로토콜 최신 스펙 확인
- Google ADK to_a2a() API 검증
- Agent Card JSON Schema 2026년 확인

예시:
"A2A 통합 전 2026년 스펙 웹 검색"
"to_a2a() API 시그니처 재검증"
```

#### 3.2 구현 후 (Review)

##### 🏗️ Full Stack Review

```markdown
Agent: code-reviewer
호출: Task tool with subagent_type="code-reviewer"

사용 시점: E2E 테스트 작성 후

이유:
- Extension → Server → MCP/A2A 전체 흐름 검증
- 아키텍처 일관성 최종 확인
- Zombie Task 방지 로직 검증
- Async Thread Isolation 확인

예시:
"Phase 3 완료, 전체 스택 리뷰"
```

##### 🏁 Phase DoD Verification

```markdown
Agent: phase-orchestrator
호출: Task tool with subagent_type="phase-orchestrator"

검증 항목:
- [ ] 긴 응답 생성 중 탭 닫기 시 서버 로그에 "Task Cancelled"
- [ ] 무거운 도구 실행 중에도 /health 즉시 응답
- [ ] A2A Agent Card 교환 성공
- [ ] E2E 시나리오 통과
- [ ] src/README.md에 A2A 아키텍처 추가
- [ ] src/adapters/README.md에 A2A 어댑터 추가
- [ ] tests/README.md에 E2E 테스트 섹션 추가
```

---

## 선택적 활용 (상황별)

### 문서 최적화

```markdown
Skill: claudemd-optimization
호출: /claudemd-optimization

사용 시점: CLAUDE.md가 200줄 초과 시

이유:
- humanlayer.dev 베스트 프랙티스 기반 정리
- 컨텍스트 효율성 향상
- 장황한 내용을 간결하게 변환

예시:
"CLAUDE.md 최적화 필요, 현재 250줄"
```

### 의사결정 지원

```markdown
Skill: decision-helper
호출: /decision-helper

사용 시점: 기술 선택 고민 시

이유:
- 선택지 구조화
- 트레이드오프 명확화
- ADHD/선택장애 친화적 정리

예시:
"SQLite vs PostgreSQL 선택 고민"
"Streamable HTTP vs SSE 선택 고민"
```

### 코드 이해

```markdown
Skill: code-explainer
호출: /code-explainer

사용 시점: 복잡한 기존 코드 파악 시

이유:
- Mermaid 다이어그램 자동 생성
- 구조화된 마크다운 설명
- 신규 팀원 온보딩 시 유용

예시:
"DynamicToolset 구현 로직 설명 필요"
"Async Factory Pattern 이해 필요"
```

---

## 자동 트리거 설정

### CLAUDE.md 자동 호출 규칙 (권장)

```markdown
## 자동 Skill/Agent 호출 규칙

| 사용자 입력 패턴 | 자동 호출 | 이유 |
|-----------------|---------|------|
| "Implement [Entity/Service]" | /tdd | TDD 필수 |
| "ADK/MCP 코드 작성" | /mcp-adk-standards | API 검증 |
| "보안 코드 완료" | security-reviewer | 취약점 점검 |
| "Phase X 완료" | phase-orchestrator | DoD 검증 |
| "아키텍처 변경" | adr-specialist | 결정 기록 |
| "Adapter 구현" | hexagonal-patterns | 패턴 검증 |
```

### Claude Code Settings 연동

```json
{
  "customPrompts": {
    "implementEntity": {
      "trigger": "Implement.*Entity|Service",
      "action": "invoke_skill:tdd"
    },
    "mcpCode": {
      "trigger": "ADK|MCP|DynamicToolset",
      "action": "invoke_skill:mcp-adk-standards"
    },
    "securityCode": {
      "trigger": "Token|Auth|CORS|Security",
      "action": "invoke_skill:security-checklist"
    }
  }
}
```

---

## 핵심 원칙

### 1. Standards Verification은 Plan과 구현 양쪽 모두

```
Plan 단계 → 웹 검색 (아키텍처 방향 확인)
    ↓
구현 단계 → 웹 검색 (API 시그니처 재검증)
```

**이유:** MCP/ADK는 빠르게 변하므로 Plan 시점의 정보가 구현 시점에 outdated될 수 있음.

### 2. TDD는 모든 구현 전

```
요구사항 → 테스트 작성 (Red) → 구현 (Green) → 리팩토링 (Refactor)
```

**적용 대상:** Entity, Service, Adapter 모두

### 3. Security Review는 보안 코드 작성 후

```
보안 코드 작성 → security-reviewer 호출 → 취약점 수정 → 재검토
```

**대상:**
- Token Handshake
- CORS 설정
- Auth Middleware
- Input Validation

### 4. Phase DoD는 Phase 완료 시

```
Phase 작업 완료 → phase-orchestrator 호출 → DoD 검증 → 다음 Phase 이행
```

**검증 항목:**
- 테스트 커버리지
- 문서화 완성도
- 보안 체크리스트
- 아키텍처 준수

### 5. ADR은 아키텍처 결정 시

```
기술 선택 고민 → decision-helper (선택적) → 결정 → adr-specialist 호출 → ADR 생성
```

**대상:**
- Transport Protocol 선택
- Database 선택
- 보안 패턴 선택
- 아키텍처 변경

---

## Phase별 우선순위 요약

| Phase | 필수 Skill/Agent | 선택적 | 문서화 |
|-------|-----------------|--------|--------|
| **Phase 2** | mcp-adk-standards, tdd, hexagonal-patterns, code-reviewer, phase-orchestrator | adr-specialist, decision-helper | src/adapters/README.md 생성 |
| **Phase 2.5** | security-checklist, security-reviewer, tdd, phase-orchestrator | code-explainer | extension/README.md 생성 |
| **Phase 3** | mcp-adk-standards, code-reviewer, phase-orchestrator | - | E2E 테스트 문서 추가 |

---

## 참고 문서

- [roadmap.md](roadmap.md) - Phase별 상세 계획
- [implementation-guide.md](implementation-guide.md) - 구현 패턴
- [architecture.md](architecture.md) - 헥사고날 아키텍처
- [standards-verification.md](standards-verification.md) - 표준 검증 프로토콜

---

*문서 생성일: 2026-01-29*
