---
name: mcp-scaffold
description: FastMCP 기반 MCP 서버 프로젝트를 생성합니다. 새 MCP 서버 개발 시작 시 사용하세요.
argument-hint: <server-name> [--tools tool1,tool2]
---

# MCP 서버 스캐폴딩

서버 이름: `$0`
도구 목록: `$1` (선택)

## 생성 구조

```
mcp-servers/$0/
├── pyproject.toml
├── README.md
├── src/
│   └── $0/
│       ├── __init__.py
│       ├── server.py
│       └── tools/
│           ├── __init__.py
│           └── [tool_name].py
└── tests/
    ├── __init__.py
    └── test_server.py
```

## 생성 파일 내용

### pyproject.toml

```toml
[project]
name = "$0"
version = "0.1.0"
description = "MCP Server: $0"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=0.1.0",
]

[project.scripts]
$0 = "$0.server:main"
```

### server.py

```python
from fastmcp import FastMCP

mcp = FastMCP("$0")

# 도구 정의는 tools/ 디렉토리에서 import
from .tools import *

def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
```

### tools/example.py

```python
from .. import mcp

@mcp.tool()
def example_tool(param: str) -> str:
    """도구 설명

    Args:
        param: 파라미터 설명

    Returns:
        결과 설명
    """
    return f"Result: {param}"
```

## 도구 옵션 처리

`--tools resize,convert,compress` 형식으로 전달 시:

```python
# tools/resize.py
@mcp.tool()
def resize(width: int, height: int) -> dict:
    """이미지 리사이즈"""
    pass

# tools/convert.py
@mcp.tool()
def convert(format: str) -> dict:
    """포맷 변환"""
    pass
```

## 생성 후 안내

```markdown
# $0 MCP 서버 생성 완료

## 시작하기

1. 의존성 설치:
   ```bash
   cd mcp-servers/$0
   pip install -e .
   ```

2. 서버 실행:
   ```bash
   $0
   ```

3. 테스트:
   ```bash
   /mcp-test http://localhost:8000
   ```

## 다음 단계

- `src/$0/tools/`에 도구 추가
- `tests/`에 테스트 작성
- README.md 업데이트
```

## 참고

- [FastMCP 문서](https://gofastmcp.com/)
- [MCP 스펙](https://modelcontextprotocol.io/)
