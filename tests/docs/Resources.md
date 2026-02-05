# **📊 Test Resources**

## **MCP Servers**

| Type | Endpoint | Auth | 용도 |
| :---- | :---- | :---- | :---- |
| **Local (Synapse)** | http://127.0.0.1:9000/mcp | None | 기본 MCP 테스트 |
| **Local (Multi-port)** | http://127.0.0.1:9001/mcp | API Key | 인증 테스트 |
| **Local (Multi-port)** | http://127.0.0.1:9002/mcp | OAuth 2.0 | OAuth 테스트 |
| **External (MCP Apps)** | https://remote-mcp-server-authless.idosalomon.workers.dev/mcp | None | Phase 6-B 검증 |

**로컬 MCP 서버 프로젝트 위치:**

C:\\Users\\sungb\\Documents\\GitHub\\MCP\_SERVER\\MCP\_Streamable\_HTTP

**Multi-port 설정:**

* 포트 9000: No auth (기본값)  
* 포트 9001: API Key (X-API-Key 헤더)  
* 포트 9002: OAuth 2.0 (Authorization: Bearer \<token\>)

## **A2A Agents**

| Type | Endpoint | 용도 |
| :---- | :---- | :---- |
| **Echo Agent** | http://127.0.0.1:9003 | A2A 기본 테스트 |
| **Math Agent** | Dynamic port | A2A 수학 테스트 |

**실행 방법:** tests/conftest.py에서 subprocess로 자동 시작됨.

## **📚 References**

* [pytest Documentation](https://docs.pytest.org/)  
* [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)  
* [pytest-cov](https://pytest-cov.readthedocs.io/)  
* [Hexagonal Architecture Testing](https://alistair.cockburn.us/hexagonal-architecture/)  
* [TDD Best Practices](https://www.builder.io/blog/test-driven-development-ai)