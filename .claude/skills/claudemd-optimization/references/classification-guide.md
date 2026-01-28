# 섹션 분류 가이드

## 목차

1. [KEEP - CLAUDE.md에 유지](#-keep---claudemd에-유지)
2. [MOVE - docs/로 이동](#-move---docs로-이동)
3. [DELETE - 삭제](#-delete---삭제)
4. [파일 위치 옵션](#파일-위치-옵션)

---

## 🟢 KEEP - CLAUDE.md에 유지

**보편적으로 적용되는 내용만** 유지:

| 항목 | 예시 |
|------|------|
| 프로젝트명, 목적, 소유자 | "AgentHub - Google ADK 기반 Agent 시스템" |
| 고수준 디렉토리 구조 | src/, tests/, docs/ 트리 |
| 환경 변수 (목록만) | `API_KEY`, `DATABASE_URL` |
| 시스템 의존성 | Python 3.10+, Node 18+ |
| 범용 명령어 | `bun test`, `bun build`, `pytest` |
| 설계 원칙 (3-5개) | "Hexagonal Architecture", "DI 사용" |
| 중요 파일 참조 (테이블) | 역할 → 파일 매핑 |
| Progressive disclosure 테이블 | 주제 → docs/ 참조 |
| 프로젝트 규칙 (3-5개) | "한국어로 소통", "웹 검색 적극 활용" |

### 판단 기준

✅ **유지**: "이 프로젝트의 모든 작업에 적용되는가?"

```markdown
# 좋은 예
- "TypeScript monorepo임"
- "`bun test`로 테스트 실행"
- "Hexagonal Architecture 사용"
```

---

## 🟡 MOVE - docs/로 이동

**작업별 세부사항**은 별도 문서로:

| 내용 유형 | 대상 파일 |
|----------|----------|
| 명령어/에이전트 상세 목록 | `docs/commands-and-agents.md` |
| 에이전트 스펙 | `docs/agent-specs.md` |
| API 패턴과 예시 | `docs/api-patterns.md` |
| 도구별 가이드 | `docs/{tool}-guide.md` |
| 프로토콜 문서 | `docs/{protocol}-protocol.md` |
| 버전 히스토리 | `docs/release-history.md` |
| 아키텍처 심층 분석 | `docs/architecture-guide.md` |
| 테스트 전략 | `docs/testing-strategy.md` |

### 판단 기준

🟡 **이동**: "특정 작업 유형에서만 필요한가?"

```markdown
# 이동 대상 예
- "인증 구현 시 JWT 사용" → docs/auth-guide.md
- "API 엔드포인트 상세 목록" → docs/api-patterns.md
- "MCP 프로토콜 명세" → docs/mcp-protocol.md
```

---

## 🔴 DELETE - 삭제

**노이즈 제거**:

| 항목 | 이유 |
|------|------|
| 중복 정보 | 같은 내용 반복 |
| 구식 내용 | 더 이상 유효하지 않음 |
| 작업별 지시 | docs/로 이동하거나 삭제 |
| 인라인 코드 스니펫 | 파일 참조 사용 |
| 스타일/포매팅 규칙 | 린터 도구 사용 |
| 장황한 설명 | 간결하게 축약 |
| 자동 생성 boilerplate | 수동 큐레이션 필요 |

### 판단 기준

🔴 **삭제**: "Claude가 이미 알고 있거나, 도구가 처리하거나, 구식인가?"

```markdown
# 삭제 대상 예
- "2칸 들여쓰기 사용" → ESLint/Prettier가 처리
- "const 선호" → 기존 코드에서 학습
- "v1.0.0 릴리스 노트 상세" → 불필요
```

---

## 분류 체크리스트

섹션 분류 시 순서대로 질문:

```
1. 모든 작업에 적용? → Yes: KEEP
                      → No: 다음 질문

2. 특정 작업에 유용? → Yes: MOVE to docs/
                      → No: 다음 질문

3. Claude가 이미 앎?  → Yes: DELETE
   도구가 처리?       → Yes: DELETE
   구식/중복?         → Yes: DELETE
```

---

## 파일 위치 옵션

### CLAUDE.md 배치 위치

| 위치 | 용도 | git 관리 |
|------|------|----------|
| `./CLAUDE.md` | 프로젝트 루트 (팀 공유) | ✅ 체크인 권장 |
| `./CLAUDE.local.md` | 개인 설정 | ❌ .gitignore |
| `~/.claude/CLAUDE.md` | 글로벌 (모든 세션) | - |

### 모노레포 구조

```
monorepo/
├── CLAUDE.md           # 루트 공통 설정
├── apps/
│   ├── frontend/
│   │   └── CLAUDE.md   # 프론트엔드 전용
│   └── backend/
│       └── CLAUDE.md   # 백엔드 전용
```

Claude는 실행 위치에서 상위로 올라가며 모든 CLAUDE.md를 로드함.

### @import로 분리

```markdown
# CLAUDE.md (루트)
See @docs/architecture.md for architecture details.
See @.claude/team-rules.md for team conventions.
```
