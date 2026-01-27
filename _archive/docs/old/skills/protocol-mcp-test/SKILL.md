---
name: mcp-test
description: MCP 서버의 연결 및 도구 호출을 테스트합니다. MCP 서버 개발 후 검증 시 사용하세요.
argument-hint: <server-url> [--tool name] [--list-tools]
---

# MCP 서버 테스트

서버 URL: `$0`
옵션: `$ARGUMENTS`

## 테스트 유형

### 1. 연결 테스트

서버에 연결하여 기본 통신 확인:

```bash
# Streamable HTTP 연결 테스트
curl -X POST $0/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```

### 2. 도구 목록 조회 (--list-tools)

```bash
curl -X POST $0/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 2}'
```

### 3. 특정 도구 테스트 (--tool name)

```bash
curl -X POST $0/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "tool_name",
      "arguments": {}
    },
    "id": 3
  }'
```

## 테스트 절차

1. **서버 상태 확인**
   - 서버가 실행 중인지 확인
   - 포트가 올바른지 확인

2. **초기화 테스트**
   - `initialize` 메서드 호출
   - 서버 정보 및 capabilities 확인

3. **도구 목록 확인**
   - `tools/list` 메서드 호출
   - 등록된 도구 목록 출력

4. **도구 호출 테스트**
   - 각 도구별 샘플 호출
   - 응답 형식 확인

## 출력 형식

```markdown
# MCP 서버 테스트 결과

## 서버 정보
- URL: $0
- 상태: 연결됨/실패

## 서버 Capabilities
- tools: 지원
- resources: 지원
- prompts: 미지원

## 등록된 도구 (N개)

| 도구명 | 설명 | 파라미터 |
|--------|------|----------|
| search | 문서 검색 | query: string |
| ... | ... | ... |

## 도구 테스트 결과

### search
- 입력: {"query": "test"}
- 출력: {"results": [...]}
- 상태: ✅ 성공

### ...
```

## 일반적인 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| Connection refused | 서버 미실행 | 서버 시작 |
| 404 Not Found | 잘못된 경로 | /mcp 경로 확인 |
| Parse error | JSON 형식 오류 | 요청 형식 확인 |
| Method not found | 미구현 메서드 | 서버 코드 확인 |

## 참고

- [MCP 프로토콜 스펙](https://modelcontextprotocol.io/)
- [Streamable HTTP Transport](https://modelcontextprotocol.io/specification/transport)
