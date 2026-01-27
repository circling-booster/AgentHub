---
name: commit
description: 스테이징된 변경사항을 분석하여 semantic commit 메시지를 생성하고 커밋합니다. 코드 변경 후 커밋할 때 사용하세요.
argument-hint: [commit-message-hint]
disable-model-invocation: true
---

# Semantic Commit 생성

## 현재 상태 확인

먼저 현재 Git 상태를 확인합니다:

```bash
git status --short
git diff --cached --stat
```

## 커밋 타입

변경 내용에 따라 적절한 타입을 선택합니다:

| 타입 | 용도 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 포맷팅 (기능 변경 없음) |
| `refactor` | 리팩토링 (기능 변경 없음) |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 등 기타 변경 |

## 작업 절차

1. **변경사항 분석**
   - `git diff --cached`로 스테이징된 변경 확인
   - 변경의 목적과 영향 파악

2. **커밋 메시지 작성**
   - 형식: `<type>(<scope>): <subject>`
   - scope는 선택적 (변경된 모듈/파일)
   - subject는 명령형, 소문자 시작, 마침표 없음

3. **인자 처리**
   - `$ARGUMENTS`가 있으면 힌트로 활용
   - 없으면 변경사항에서 메시지 자동 생성

4. **커밋 실행**
   ```bash
   git commit -m "<type>(<scope>): <subject>"
   ```

## 예시

```bash
# 기능 추가
git commit -m "feat(auth): add JWT token validation"

# 버그 수정
git commit -m "fix(api): handle null response from server"

# 문서 업데이트
git commit -m "docs(readme): update installation instructions"

# 리팩토링
git commit -m "refactor(utils): simplify date formatting logic"
```

## 주의사항

- 스테이징된 변경이 없으면 커밋하지 않음
- 민감한 정보(.env, credentials)가 포함되어 있으면 경고
- 커밋 전 변경사항 요약을 사용자에게 보여줌
