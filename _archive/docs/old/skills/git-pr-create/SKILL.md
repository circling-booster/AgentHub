---
name: pr-create
description: Pull Request를 생성합니다. 브랜치 작업 완료 후 PR 생성 시 사용하세요.
argument-hint: [target-branch]
disable-model-invocation: true
---

# Pull Request 생성

## 현재 상태 확인

```bash
git status
git log --oneline -5
git branch -vv
```

## PR 생성 절차

### 1. 변경사항 분석
- 현재 브랜치의 모든 커밋 확인
- 대상 브랜치(기본: main)와의 diff 확인

### 2. PR 정보 작성

**제목**: 70자 이내, 변경 내용 요약
**본문**:
```markdown
## Summary
- 주요 변경사항 1-3개 bullet points

## Test plan
- [ ] 테스트 항목 1
- [ ] 테스트 항목 2
```

### 3. PR 생성

```bash
gh pr create --title "제목" --body "본문"
```

대상 브랜치 지정:
```bash
gh pr create --base $ARGUMENTS --title "제목" --body "본문"
```

## 출력

- PR URL 제공
- 리뷰어 지정 안내
