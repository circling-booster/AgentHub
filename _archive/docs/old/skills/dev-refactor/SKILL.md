---
name: refactor
description: 코드 리팩토링을 제안합니다. 코드 품질 개선, 구조 정리 시 사용하세요.
argument-hint: [file-or-function]
---

# 리팩토링 제안

대상: `$ARGUMENTS`

## 분석 관점

### 1. 코드 스멜
- 중복 코드
- 긴 함수/클래스
- 과도한 파라미터
- 복잡한 조건문

### 2. 설계 원칙
- 단일 책임 원칙 (SRP)
- 개방-폐쇄 원칙 (OCP)
- DRY (Don't Repeat Yourself)

### 3. 가독성
- 명확한 네이밍
- 적절한 추상화 수준
- 일관된 스타일

## 리팩토링 기법

| 기법 | 적용 상황 |
|------|----------|
| Extract Function | 긴 함수 분리 |
| Rename | 불명확한 이름 |
| Inline | 불필요한 추상화 제거 |
| Replace Conditional | 복잡한 조건문 단순화 |

## 출력 형식

```markdown
## 리팩토링 제안

### 현재 문제점
1. [문제 1]
2. [문제 2]

### 제안 변경
1. [변경 1]: [이유]
2. [변경 2]: [이유]

### Before/After
[코드 비교]

### 기대 효과
- [효과]
```
