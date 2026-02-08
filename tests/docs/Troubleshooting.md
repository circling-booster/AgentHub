# **🐛 Troubleshooting**

### **MCP 서버 연결 실패**

1. **로컬 MCP 서버 실행 확인**  
   cd path/to/MCP\_Streamable\_HTTP  
   python \-m synapse  \# 기본 포트 9000

2. **포트 충돌 확인**  
   netstat \-ano | findstr :9000

3. **환경변수 오버라이드**  
   MCP\_TEST\_PORT=8888 pytest tests/integration/

### **LLM 테스트 실패**

1. **API 키 확인**: .env 파일에 OPENAI\_API\_KEY 존재 여부 확인  
2. **환경변수 로딩**: pytest \-v \--log-cli-level=DEBUG로 디버깅  
3. **API 유효성**: curl 등으로 키 테스트

### **SQLite Database Locked**

1. **WAL 파일 삭제**: rm data/agenthub.db-wal data/agenthub.db-shm  
2. **격리 확인**: authenticated\_client fixture를 사용하여 독립 DB를 쓰고 있는지 확인

### **anyio plugin 에러**

* pyproject.toml에 `anyio_mode = "auto"`가 설정되어 있는지 확인하십시오.
* `@pytest.mark.asyncio` 마커가 남아있지 않은지 확인 (anyio plugin과 충돌)
* asyncio API (create_task, gather 등)는 anyio가 기본 backend로 사용하여 정상 동작

### **MCP SDK anyio Cancel Scope Error**

**증상:**
- `RuntimeError: No response returned`
- `Attempted to exit cancel scope in a different task than it was entered in`
- 테스트가 응답 없이 hang되거나 teardown 시 에러 발생

**발생 조건:**
- 인증이 필요한 MCP 서버 (포트 9001, API Key/OAuth)에 연결 시
- `authenticated_client` fixture를 사용하는 async 테스트

**원인:**
- MCP Python SDK의 알려진 버그
- anyio의 cancel scope가 서로 다른 task에서 enter/exit 시도
- TestClient + anyio + MCP SDK 조합에서 발생

**관련 이슈:**
- [MCP SDK Issue #521](https://github.com/modelcontextprotocol/python-sdk/issues/521)
- [Google ADK Issue #2196](https://github.com/google/adk-python/issues/2196)
- [MCP SDK Issue #577](https://github.com/modelcontextprotocol/python-sdk/issues/577)

**임시 조치:**
- 영향받는 테스트에 `@pytest.mark.skip` 추가 (예: `test_register_mcp_with_api_key_via_api`)
- 업스트림 버그 수정 대기 중
- 무인증 서버(포트 9000) 테스트는 정상 동작

**회피 방법:**
1. Mock 사용: CI 환경처럼 `mock_mcp_toolset_in_ci` fixture 활용
2. 테스트 범위 축소: 인증 없는 서버만 테스트
3. Upstream 버그 수정 후 재활성화

### **Import 에러 (ModuleNotFoundError)**

* **원인**: from domain... 처럼 src. 접두사 없이 import한 경우
* **해결**: 프로젝트 표준인 from src.domain... 형식을 사용하십시오.