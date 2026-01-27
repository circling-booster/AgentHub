---
name: quality-check
description: 코드 품질을 종합 분석합니다. 복잡도, 중복, 유지보수성 점검 시 사용하세요.
argument-hint: [path]
---

# 코드 품질 분석

대상: `$ARGUMENTS` (기본: 전체)

## 분석 항목

### 1. 복잡도 (Cyclomatic Complexity)
```bash
# radon 사용
radon cc src/ -a -s
```

| 등급 | 복잡도 | 평가 |
|------|--------|------|
| A | 1-5 | 단순, 좋음 |
| B | 6-10 | 적당 |
| C | 11-20 | 복잡 |
| D | 21+ | 매우 복잡, 리팩토링 필요 |

### 2. 중복 코드
```bash
# pylint 중복 검사
pylint --disable=all --enable=duplicate-code src/
```

### 3. 유지보수성 지수
```bash
radon mi src/ -s
```

### 4. 코드 라인 수
```bash
cloc src/
```

## 출력 형식

```markdown
## 코드 품질 보고서

### 요약
| 지표 | 값 | 평가 |
|------|-----|------|
| 평균 복잡도 | X | A/B/C/D |
| 중복률 | X% | 좋음/주의 |
| 유지보수성 | X | A/B/C |

### 개선 필요 파일
1. [파일]: 복잡도 높음
2. [파일]: 중복 코드

### 권장 조치
- [구체적 개선 제안]
```
