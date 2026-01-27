# FHLY Skills 디렉토리

이 디렉토리는 FHLY 프로젝트 개발을 위한 Claude Code Skills를 포함합니다.

## 디렉토리 구조

**참고:** Claude Code 공식 스펙에 따라 평탄한(flat) 구조를 사용합니다.

```
.claude/skills/
├── README.md                     # 이 파일
│
├── dev-debug/SKILL.md            # 디버깅 지원
├── dev-explain/SKILL.md          # 코드 설명
├── dev-refactor/SKILL.md         # 리팩토링 지원
│
├── docs-changelog/SKILL.md       # 변경 로그 생성
├── docs-document/SKILL.md        # 문서 작성
│
├── git-commit/SKILL.md           # 커밋 생성
├── git-pr-create/SKILL.md        # PR 생성
├── git-pr-fetch/SKILL.md         # PR 가져오기
│
├── project-overview/SKILL.md     # 프로젝트 개요
├── skill-creator/SKILL.md        # 스킬 생성 가이드
│
├── protocol-a2a-card/SKILL.md    # A2A 카드 생성
├── protocol-a2a-validate/SKILL.md # A2A 검증
├── protocol-adk-workflow/SKILL.md # ADK 워크플로우
├── protocol-demo-generate/SKILL.md # 데모 생성
├── protocol-mcp-scaffold/SKILL.md # MCP 스캐폴딩
├── protocol-mcp-test/SKILL.md    # MCP 테스트
├── protocol-mcp-tool/SKILL.md    # MCP 툴 생성
│
├── quality-check/SKILL.md        # 품질 종합 검사
├── quality-lint/SKILL.md         # 린트 실행
├── quality-review/SKILL.md       # 코드 리뷰
├── quality-test/SKILL.md         # 테스트 실행
│
└── tdd/SKILL.md                  # TDD 워크플로우
```

### 스킬 카테고리

- **dev-***: 개발 지원 (디버깅, 설명, 리팩토링)
- **docs-***: 문서화 (문서 작성, 변경 로그)
- **git-***: Git 작업 (커밋, PR)
- **protocol-***: MCP/A2A/ADK 특화 기능
- **quality-***: 코드 품질 관리
- **project-***: 프로젝트 관리
- **기타**: TDD, 스킬 생성

## Skill 파일 형식

각 SKILL.md 파일은 다음 형식을 따릅니다:

```yaml
---
name: skill-name
description: Skill의 용도와 사용 시점
argument-hint: [선택적] 인자 힌트
allowed-tools: [선택적] 허용 도구 목록
disable-model-invocation: [선택적] true/false
---

# 지시사항

$ARGUMENTS를 사용하여...
```

## YAML Frontmatter 필드

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | 권장 | Skill 이름 (생략 시 디렉토리명 사용) |
| `description` | 권장 | Skill 용도 설명 |
| `argument-hint` | 선택 | 자동완성 시 표시할 힌트 |
| `allowed-tools` | 선택 | 허용할 도구 목록 (쉼표 구분) |
| `disable-model-invocation` | 선택 | true면 수동 호출만 가능 |
| `user-invocable` | 선택 | false면 슬래시 메뉴에서 숨김 |
| `context` | 선택 | `fork`면 서브에이전트 컨텍스트 |
| `agent` | 선택 | 서브에이전트 타입 지정 |

## 변수

| 변수 | 설명 |
|------|------|
| `$ARGUMENTS` | 전체 인자 문자열 |
| `$ARGUMENTS[N]` | N번째 인자 (0부터 시작) |
| `$0`, `$1`, ... | `$ARGUMENTS[N]` 단축형 |

## 커스텀 Skill 추가

**참고:** Claude Code 공식 스펙에 따라 `.claude/skills/` 바로 아래에 평탄한 구조로 생성합니다.

### 1. 디렉토리 생성

```bash
# 평탄한 구조로 생성 (권장)
mkdir .claude/skills/my-skill

# 카테고리를 이름에 포함하여 구분 (예시)
mkdir .claude/skills/category-my-skill
```

### 2. SKILL.md 작성

```yaml
---
name: my-skill
description: 내 커스텀 skill
---

# 지시사항

$ARGUMENTS를 처리하세요.
```

### 3. 사용

```
/my-skill 인자1 인자2
```

## 지원 파일 추가

Skill에 추가 파일이 필요한 경우:

```
my-skill/
├── SKILL.md          # 메인 지시사항
├── reference.md      # 참조 문서
├── examples.md       # 사용 예시
└── scripts/
    └── helper.py     # 유틸리티 스크립트
```

SKILL.md에서 참조:

```markdown
상세 내용은 [reference.md](reference.md) 참조
```

## 동적 컨텍스트 주입

명령 실행 결과를 프롬프트에 삽입:

```markdown
## 현재 상태
- Git 상태: !`git status --short`
- 변경 파일: !`git diff --name-only`

위 정보를 바탕으로 작업하세요.
```

## 우선순위

Skills가 여러 위치에 정의된 경우 우선순위:

1. Enterprise (조직 설정)
2. Personal (`~/.claude/skills/`)
3. Project (`.claude/skills/`)

## 폴더 구조 스펙

**FHLY는 Claude Code 공식 스펙을 준수합니다:**

- ✅ **평탄한(flat) 구조**: `.claude/skills/` 바로 아래에 스킬 폴더 배치
- ❌ **중첩 카테고리 폴더**: 공식적으로 지원되지 않음
- 💡 **카테고리 구분**: 폴더명에 접두사 포함 (예: `dev-debug`, `protocol-mcp-test`)
- 📁 **스킬 내부 하위 폴더**: `scripts/`, `references/`, `assets/` 등은 권장됨

자세한 내용은 [Claude Code Skills 공식 문서](https://code.claude.com/docs/en/skills)를 참조하세요.

## 참고 자료

- [Skills 사용 가이드](../../docs/skills-guide.md)
- [에이전트 활용 가이드](../../docs/agents-guide.md)
- [Claude Code Skills 공식 문서](https://code.claude.com/docs/en/skills)
