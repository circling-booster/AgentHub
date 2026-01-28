"""AgentHub API 서버 엔트리포인트

실행 방법:
    uvicorn src.main:app --host localhost --port 8000
"""

from src.adapters.inbound.http.app import create_app

app = create_app()
