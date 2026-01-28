---
name: claudemd-optimization
description: |
  CLAUDE.md 최적화 도구. humanlayer.dev 베스트 프랙티스 기반으로 장황한 CLAUDE.md를 간결하고 효과적인 형태로 변환.

  사용 시점: (1) /init 실행 후 자동 생성된 CLAUDE.md 정리, (2) 기존 CLAUDE.md가 200줄 초과,
  (3) "optimize claude.md", "claude.md 최적화", "개선 claude.md" 등 요청 시
---

# CLAUDE.md Optimization

> 출처: [Writing a Good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

## 핵심 원칙

**LLM은 Stateless** - CLAUDE.md에 넣은 토큰만 모델이 인식함. 모든 대화에 자동 삽입되므로 최고 레버리지 포인트.

| 원칙 | 설명 |
|------|------|
| **Less Is More** | 60-150줄 목표. 명령어 150개 초과 시 전체 준수율 저하 |
| **3차원 커버** | WHAT(기술스택) + WHY(목적) + HOW(빌드/테스트) |
| **Progressive Disclosure** | 상세 내용은 별도 문서로 분리, `@path/file` 참조 |
| **상단 배치** | 중요 규칙은 CLAUDE.md 시작 부분에 |
| **강조 기법** | 핵심 규칙에 "IMPORTANT", "YOU MUST" 사용 |
| **린터 아님** | 스타일 규칙은 Biome/ESLint에 위임 |

상세 원칙: [references/principles.md](references/principles.md)

---

## 최적화 워크플로우

### Phase 1: 분석

```
1. CLAUDE.md 읽기
2. 라인 수 확인 (목표: 60-150줄)
3. 섹션 목록 추출 (## 헤더 기준)
```

### Phase 2: 분류

각 섹션을 분류:

| 분류 | 기준 | 조치 |
|------|------|------|
| 🟢 KEEP | 프로젝트명, 구조, 빌드 명령어, 핵심 원칙 | 유지 |
| 🟡 MOVE | 상세 API, 프로토콜, 버전 히스토리 | docs/로 이동 |
| 🔴 DELETE | 스타일 규칙, 중복, 구식 정보 | 삭제 |

분류 상세 가이드: [references/classification-guide.md](references/classification-guide.md)

### Phase 3: 재구성

**기존 문서 폴더 확인:**
- `docs/` 존재 → `docs/` 사용
- `agent_docs/` 존재 → `agent_docs/` 사용
- 없으면 → `docs/` 생성

**CLAUDE.md 목표 구조:**

```markdown
# 프로젝트명

## Project Overview (WHAT)
[2-5줄: 이름, 목적, 기술스택]

## Directory Structure
[10-15줄: 핵심 디렉토리만]

## How to Work (HOW)
[10-20줄: 빌드, 테스트, 환경변수]

## Key Principles
[3-5개 bullet point]

## Documentation
[테이블: 주제 → docs/ 참조]
```

### Phase 4: 검증

```
- [ ] 60-200줄 이내
- [ ] WHAT/WHY/HOW 포함
- [ ] 스타일 규칙 없음
- [ ] 인라인 코드 예시 최소화
- [ ] @import 또는 docs/ 참조 테이블 존재
- [ ] 핵심 규칙에 IMPORTANT/YOU MUST 강조
```

---

## 변환 예시

[references/examples.md](references/examples.md) 참조

---

## 안티패턴

| 패턴 | 문제 | 해결 |
|------|------|------|
| 500줄+ | 전체 준수율 저하 | docs/ 분리 |
| 인라인 코드 블록 | 구식화 위험 | 파일 참조 사용 |
| 스타일 규칙 | 린터 역할 아님 | 삭제, 도구 사용 |
| /init 결과 그대로 | 노이즈 포함 | 수동 최적화 필수 |

---

## 공식 기능 (Anthropic)

### @import 구문

CLAUDE.md에서 다른 파일 참조 시 `@path/to/file` 구문 사용:

```markdown
## Documentation
See @docs/architecture.md for detailed architecture.
See @README.md for project overview.
```

### 파일 위치 옵션

| 위치 | 용도 |
|------|------|
| `./CLAUDE.md` | 프로젝트 루트 (git 체크인, 팀 공유) |
| `./CLAUDE.local.md` | 로컬 전용 (.gitignore 추가) |
| `~/.claude/CLAUDE.md` | 글로벌 설정 (모든 세션에 적용) |

### 강조 기법

Claude가 무시하면 안 되는 규칙에 강조 표현 사용:

```markdown
IMPORTANT: 테스트 없이 커밋하지 마세요.
YOU MUST verify API patterns against official docs.
```
