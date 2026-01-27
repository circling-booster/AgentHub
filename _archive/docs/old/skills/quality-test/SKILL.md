---
name: test
description: 테스트를 생성하거나 실행합니다. 코드 품질 보장, TDD, 커버리지 확인 시 사용하세요.
argument-hint: [generate|run|coverage] [file]
---

# 테스트 관리

명령: `$ARGUMENTS`

## 사용법

### 테스트 생성

```
/test generate src/utils/parser.py
```

대상 파일을 분석하여 pytest 기반 테스트를 생성합니다.

### 테스트 실행

```
/test run
/test run tests/test_parser.py
```

### 커버리지 확인

```
/test coverage
```

## 테스트 생성 전략

### 1. 함수 분석

- 입력 파라미터 타입
- 반환 타입
- 발생 가능한 예외
- 부작용

### 2. 테스트 케이스 유형

| 유형 | 설명 |
|------|------|
| Happy Path | 정상 입력, 예상 출력 |
| Edge Cases | 경계값 (빈 값, 최대값, 최소값) |
| Error Cases | 잘못된 입력, 예외 상황 |
| None/Null | None 입력 처리 |

### 3. 테스트 구조

```python
import pytest
from src.module import function_to_test

class TestFunctionName:
    """function_name에 대한 테스트"""

    def test_happy_path(self):
        """정상 입력에 대한 테스트"""
        result = function_to_test(valid_input)
        assert result == expected_output

    def test_edge_case_empty(self):
        """빈 입력에 대한 테스트"""
        result = function_to_test("")
        assert result == expected_for_empty

    def test_error_invalid_input(self):
        """잘못된 입력에 대한 테스트"""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

## 출력 형식

### 테스트 생성 시

```markdown
# 생성된 테스트: test_[module].py

## 테스트 대상
- 파일: src/utils/parser.py
- 함수: parse_data, validate_input

## 테스트 케이스
- test_parse_data_valid: 정상 파싱
- test_parse_data_empty: 빈 입력
- test_validate_input_invalid: 잘못된 입력

## 생성된 코드
[테스트 코드]
```

### 테스트 실행 시

```markdown
# 테스트 결과

- 총 테스트: 10개
- 통과: 8개
- 실패: 2개

## 실패한 테스트
| 테스트 | 원인 |
|--------|------|
| test_X | AssertionError: expected Y |
```

## 테스트 프레임워크

- Python: pytest
- JavaScript: jest
- Go: testing
