---
name: lint
description: 코드 스타일을 검사하고 자동 수정합니다. 코드 포맷팅, 스타일 통일 시 사용하세요.
argument-hint: [--fix] [path]
---

# 린트 검사

옵션: `$ARGUMENTS`

## Python 린터

### Ruff (권장)
```bash
# 검사
ruff check .

# 자동 수정
ruff check --fix .

# 포맷팅
ruff format .
```

### 설정 (pyproject.toml)
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.ruff.format]
quote-style = "double"
```

## JavaScript/TypeScript

### ESLint
```bash
# 검사
npx eslint .

# 자동 수정
npx eslint --fix .
```

### Prettier
```bash
npx prettier --check .
npx prettier --write .
```

## 출력 형식

```markdown
## 린트 결과

### 요약
- 검사 파일: N개
- 이슈: N개
- 자동 수정: N개

### 이슈 목록
| 파일 | 라인 | 규칙 | 메시지 |

### 자동 수정됨
- [수정된 파일 목록]
```
