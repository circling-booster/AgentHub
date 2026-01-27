---
name: document
description: API 문서, README, 사용 가이드를 생성합니다. 코드 문서화가 필요할 때 사용하세요.
argument-hint: [path-or-module]
---

# 문서 생성

대상: `$ARGUMENTS`

## 문서 유형

### README.md
```markdown
# 프로젝트명

설명 (1-2문장)

## 설치
## 사용법
## 설정
## 라이선스
```

### API 문서
```markdown
## function_name(param1, param2)

설명

**Parameters:**
| 이름 | 타입 | 필수 | 설명 |

**Returns:**
| 타입 | 설명 |

**Example:**
```

## 작업 절차

1. 대상 코드/모듈 분석
2. 공개 인터페이스 파악
3. docstring에서 정보 추출
4. 문서 템플릿 적용
5. 예제 코드 추가

## 문서화 원칙

- 명확하고 간결하게
- 예제 코드 필수 포함
- 코드와 동기화 유지
