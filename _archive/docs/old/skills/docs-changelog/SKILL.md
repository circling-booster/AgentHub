---
name: changelog
description: CHANGELOG를 자동 생성합니다. 릴리스 준비 시 사용하세요.
argument-hint: [version]
---

# CHANGELOG 생성

버전: `$ARGUMENTS` (없으면 Unreleased)

## 분석 대상

```bash
git log --oneline --since="last tag"
```

## CHANGELOG 형식

```markdown
# Changelog

## [Unreleased]

### Added
- 새 기능

### Changed
- 변경된 기능

### Fixed
- 버그 수정

### Removed
- 제거된 기능

## [1.0.0] - YYYY-MM-DD
...
```

## 커밋 분류

| 커밋 타입 | CHANGELOG 섹션 |
|----------|---------------|
| feat | Added |
| fix | Fixed |
| refactor | Changed |
| remove | Removed |
| docs | (문서만 변경시 생략) |

## 작업 절차

1. 이전 태그 이후 커밋 조회
2. 커밋 타입별 분류
3. 사용자 관점 설명으로 변환
4. CHANGELOG.md 업데이트
