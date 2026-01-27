---
name: pr-fetch
description: PR 정보를 가져와 분석합니다. PR 리뷰 전 내용 파악 시 사용하세요.
argument-hint: <pr-number>
---

# PR 정보 조회

PR 번호: `$ARGUMENTS`

## 조회 명령

```bash
gh pr view $ARGUMENTS
gh pr diff $ARGUMENTS
gh pr view $ARGUMENTS --comments
```

## 분석 내용

1. **PR 개요**: 제목, 설명, 상태
2. **변경 파일**: 수정된 파일 목록
3. **diff 분석**: 주요 변경사항 요약
4. **코멘트**: 기존 리뷰 내용

## 출력 형식

```markdown
# PR #N: [제목]

## 상태
- 작성자: @username
- 브랜치: feature -> main
- 상태: Open/Merged/Closed

## 변경 요약
- 파일 N개 변경
- +N / -N lines

## 주요 변경
1. [변경 1]
2. [변경 2]

## 리뷰 코멘트
- [기존 코멘트 요약]
```
