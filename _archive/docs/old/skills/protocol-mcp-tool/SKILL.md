---
name: mcp-tool
description: MCP 도구 정의를 생성합니다. MCP 서버에 새 도구 추가 시 사용하세요.
argument-hint: <tool-name>
---

# MCP 도구 정의 생성

도구 이름: `$ARGUMENTS`

## FastMCP 도구 형식

```python
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
def tool_name(
    param1: str,
    param2: int = 10
) -> dict:
    """도구 설명 (LLM에 표시됨)

    Args:
        param1: 파라미터 1 설명
        param2: 파라미터 2 설명 (기본값: 10)

    Returns:
        결과 설명
    """
    # 구현
    return {"result": "value"}
```

## 도구 설계 원칙

1. **명확한 이름**: 동사_목적어 형식 (search_documents)
2. **상세한 docstring**: LLM이 이해할 수 있도록
3. **타입 힌트**: 모든 파라미터와 반환값에 타입 지정
4. **에러 처리**: ToolError로 명확한 에러 반환

## 타입 지원

| Python 타입 | JSON Schema |
|------------|-------------|
| str | string |
| int | integer |
| float | number |
| bool | boolean |
| list[T] | array |
| dict | object |

## 출력

생성된 도구 코드와 테스트 방법 제공
