# Claude Code Skills 사용 가이드

이 문서는 FHLY 프로젝트에 탑재된 Claude Code Skills의 사용법을 설명합니다.

## 개요

Skills는 Claude Code에서 `/command` 형태로 호출하는 사전 정의된 명령어입니다.
`.claude/skills/<skill-name>/SKILL.md` 파일로 정의되며, 반복적인 작업을 자동화합니다.

**참고:** FHLY는 Claude Code 공식 스펙을 준수하여 평탄한(flat) 디렉토리 구조를 사용합니다.

## Skills 목록

### Git 관련

| Skill | 설명 | 사용법 |
|-------|------|--------|
| `/commit` | Semantic commit 메시지 생성 및 커밋 | `/commit` 또는 `/commit fix: 버그 수정` |
| `/pr-create` | Pull Request 생성 | `/pr-create` 또는 `/pr-create develop` |
| `/pr-fetch` | PR 정보 가져오기 및 분석 | `/pr-fetch 123` |

### 품질 관련

| Skill | 설명 | 사용법 |
|-------|------|--------|
| `/review` | 코드 리뷰 (보안, 성능, 가독성) | `/review` 또는 `/review src/main.py` |
| `/test` | 테스트 생성 및 실행 | `/test` 또는 `/test generate src/utils.py` |
| `/lint` | 코드 스타일 검사 및 수정 | `/lint` 또는 `/lint --fix` |
| `/quality-check` | 종합 품질 분석 | `/quality-check` |

### 문서 관련

| Skill | 설명 | 사용법 |
|-------|------|--------|
| `/document` | API 문서, README 생성 | `/document src/api/` |
| `/changelog` | CHANGELOG 자동 생성 | `/changelog` |

### 개발 관련

| Skill | 설명 | 사용법 |
|-------|------|--------|
| `/explain` | 코드 설명 및 분석 | `/explain src/complex.py` |
| `/debug` | 에러 분석 및 해결책 제시 | `/debug "에러 메시지"` |
| `/refactor` | 코드 리팩토링 제안 | `/refactor src/legacy.py` |

### 프로젝트 관련

| Skill | 설명 | 사용법 |
|-------|------|--------|
| `/overview` | 프로젝트 구조 분석 | `/overview` |
| `/skill-creator` | 새로운 스킬 생성 가이드 | `/skill-creator` |

### MCP/A2A/ADK 특화

| Skill | 설명 | 사용법 |
|-------|------|--------|
| `/mcp-scaffold` | MCP 서버 프로젝트 생성 | `/mcp-scaffold my-server` |
| `/mcp-tool` | MCP 도구 정의 생성 | `/mcp-tool search-docs` |
| `/mcp-test` | MCP 서버 테스트 | `/mcp-test http://localhost:8001` |
| `/a2a-card` | A2A Agent Card 생성 | `/a2a-card my-agent` |
| `/a2a-validate` | Agent Card 검증 | `/a2a-validate agent.json` |
| `/adk-workflow` | ADK 워크플로우 생성 | `/adk-workflow sequential` |
| `/demo-generate` | 데모 시나리오 생성 | `/demo-generate audio-separation` |

### 워크플로우

| Skill | 설명 | 사용법 |
|-------|------|--------|
| `/tdd` | TDD 워크플로우 실행 | `/tdd src/feature.py` |

---

## 상세 사용법

### /commit

스테이징된 변경사항을 분석하여 semantic commit 메시지를 생성합니다.

```bash
# 기본 사용 (자동 메시지 생성)
/commit

# 메시지 힌트 제공
/commit feat: 사용자 인증 추가

# 특정 타입 강제
/commit fix
```

**Commit 타입:**
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 기타 변경

---

### /review

코드를 다양한 관점에서 리뷰합니다.

```bash
# 전체 변경사항 리뷰
/review

# 특정 파일 리뷰
/review src/mcp/server.py

# 특정 관점으로 리뷰
/review --security src/auth/
```

**리뷰 관점:**
- 보안 취약점
- 성능 이슈
- 가독성/유지보수성
- 에러 핸들링
- 테스트 커버리지

---

### /test

테스트를 생성하거나 실행합니다.

```bash
# 테스트 생성
/test generate src/utils/parser.py

# 테스트 실행
/test run

# 커버리지 확인
/test coverage
```

---

### /explain

코드의 작동 방식을 상세히 설명합니다.

```bash
# 파일 전체 설명
/explain src/complex_algorithm.py

# 특정 함수 설명
/explain src/utils.py::calculate_hash

# 다이어그램 포함 설명
/explain --diagram src/architecture/
```

**출력 포함 내용:**
- 비유를 통한 개념 설명
- ASCII 다이어그램
- 단계별 흐름 설명
- 주의사항 및 함정

---

### /mcp-scaffold

FastMCP 기반 MCP 서버 프로젝트를 생성합니다.

```bash
# 기본 서버 생성
/mcp-scaffold document-search

# 도구 포함 생성
/mcp-scaffold image-processor --tools resize,convert,compress
```

**생성되는 구조:**
```
mcp-servers/document-search/
├── pyproject.toml
├── README.md
├── src/
│   └── document_search/
│       ├── __init__.py
│       ├── server.py
│       └── tools/
└── tests/
```

---

### /mcp-test

MCP 서버의 연결 및 도구 호출을 테스트합니다.

```bash
# 서버 연결 테스트
/mcp-test http://localhost:8001

# 특정 도구 테스트
/mcp-test http://localhost:8001 --tool search_documents

# 모든 도구 나열
/mcp-test http://localhost:8001 --list-tools
```

---

### /a2a-card

A2A 프로토콜 표준의 Agent Card를 생성합니다.

```bash
# Agent Card 생성
/a2a-card my-agent

# 기존 에이전트에서 생성
/a2a-card --from-code src/agents/code_agent.py
```

**생성 예시:**
```json
{
  "name": "my-agent",
  "description": "...",
  "capabilities": [...],
  "endpoints": {...}
}
```

---

### /adk-workflow

Google ADK 멀티에이전트 워크플로우를 생성합니다.

```bash
# Sequential 워크플로우
/adk-workflow sequential

# Parallel 워크플로우
/adk-workflow parallel

# Loop 워크플로우
/adk-workflow loop

# 커스텀 라우터
/adk-workflow router
```

---

### /tdd

TDD (Test-Driven Development) 워크플로우를 실행합니다.

```bash
/tdd src/new_feature.py
```

**프로세스:**
1. Red: 실패하는 테스트 작성
2. Green: 테스트 통과하는 최소 코드
3. Refactor: 코드 개선

---

## Skill 커스터마이징

**참고:** 새로운 스킬 생성 시 `/skill-creator` 명령을 사용하면 가이드를 받을 수 있습니다.

### 새 Skill 추가

```bash
# 평탄한 구조로 디렉토리 생성 (권장)
mkdir .claude/skills/my-skill

# 카테고리를 이름에 포함 (예시)
mkdir .claude/skills/category-my-skill
```

`.claude/skills/my-skill/SKILL.md`:
```yaml
---
name: my-skill
description: 내 커스텀 skill 설명
---

# 지시사항

$ARGUMENTS를 처리하세요.
```

### 기존 Skill 수정

`.claude/skills/<skill-name>/SKILL.md` 파일을 직접 편집합니다.

---

## 우선순위 가이드

| 우선순위 | Skills | 용도 |
|---------|--------|------|
| 필수 | `/commit`, `/explain`, `/overview`, `/review`, `/test` | 일상적 개발 |
| 필수 | `/mcp-scaffold`, `/mcp-test` | MCP 서버 개발 |
| 권장 | `/tdd`, `/debug`, `/refactor` | 계획적 개발 |
| 권장 | `/a2a-card`, `/adk-workflow`, `/demo-generate` | 프로토콜 작업 |
| 선택 | `/lint`, `/quality-check`, `/changelog`, `/document` | 품질 관리 및 문서화 |

---

## 참고 자료

- [Claude Code Skills 공식 문서](https://code.claude.com/docs/en/skills)
- [FHLY 에이전트 가이드](agents-guide.md)
- [Skills 디렉토리 구조](../.claude/skills/README.md)
