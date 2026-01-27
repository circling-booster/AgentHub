---
name: a2a-card
description: A2A Agent Card를 생성합니다. 에이전트를 A2A 네트워크에 등록할 때 사용하세요.
argument-hint: <agent-name>
---

# A2A Agent Card 생성

에이전트 이름: `$ARGUMENTS`

## Agent Card 형식

```json
{
  "name": "agent-name",
  "description": "에이전트 설명",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "skill-1",
      "name": "스킬 이름",
      "description": "스킬 설명",
      "inputSchema": {
        "type": "object",
        "properties": {}
      }
    }
  ],
  "endpoints": {
    "base": "https://example.com/a2a"
  }
}
```

## 필수 필드

| 필드 | 설명 |
|------|------|
| name | 에이전트 고유 이름 |
| description | 에이전트 역할 설명 |
| skills | 제공하는 기능 목록 |
| endpoints | API 엔드포인트 |

## 작업 절차

1. 에이전트 역할 정의
2. 제공할 skills 목록 작성
3. 입/출력 스키마 정의
4. JSON 파일 생성

## 참고

- [A2A Protocol Spec](https://github.com/a2aproject/A2A)
