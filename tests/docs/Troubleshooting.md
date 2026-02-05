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

### **pytest-asyncio 에러**

* pyproject.toml에 asyncio\_mode \= "auto"가 설정되어 있는지 확인하십시오.

### **Import 에러 (ModuleNotFoundError)**

* **원인**: from domain... 처럼 src. 접두사 없이 import한 경우  
* **해결**: 프로젝트 표준인 from src.domain... 형식을 사용하십시오.