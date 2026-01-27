---
name: tdd
description: TDD(Test-Driven Development) 워크플로우를 실행합니다. Red-Green-Refactor 사이클로 개발 시 사용하세요.
argument-hint: <feature-or-file>
---

# TDD 워크플로우

대상: `$ARGUMENTS`

## TDD 사이클

### 1. RED - 실패하는 테스트 작성

```python
def test_feature_does_something():
    """기능 설명"""
    result = feature_function(input)
    assert result == expected  # 아직 구현 안됨 -> 실패
```

테스트 실행하여 실패 확인:
```bash
pytest tests/test_feature.py -v
```

### 2. GREEN - 테스트 통과하는 최소 코드

```python
def feature_function(input):
    """최소 구현"""
    return expected  # 테스트 통과하는 가장 단순한 코드
```

테스트 실행하여 통과 확인:
```bash
pytest tests/test_feature.py -v
```

### 3. REFACTOR - 코드 개선

- 중복 제거
- 명확한 이름
- 구조 개선
- **테스트는 계속 통과해야 함**

```bash
pytest tests/test_feature.py -v  # 여전히 통과
```

## 반복

1. 다음 테스트 케이스 추가 (RED)
2. 구현 확장 (GREEN)
3. 리팩토링 (REFACTOR)
4. 반복...

## TDD 원칙

- 테스트 없이 프로덕션 코드 작성 금지
- 실패하는 테스트 하나만 작성
- 테스트 통과에 필요한 최소 코드만 작성

## 출력

각 사이클마다:
```markdown
### Cycle N

**RED**: test_xxx 작성 -> 실패 ❌
**GREEN**: xxx 구현 -> 통과 ✅
**REFACTOR**: [수행한 리팩토링] -> 통과 ✅
```
