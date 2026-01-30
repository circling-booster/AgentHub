⚠️ 알려진 제약사항 (Phase 3에서 해결)
Zombie Task (SSE 연결 해제 미처리)

현재: 클라이언트 연결 해제 시 서버 태스크 계속 실행
계획: Phase 3.1에서 Request.is_disconnected() 적용
동기식 MCP 도구 블로킹

현재: 메인 이벤트 루프 차단 가능성
계획: Phase 3.2에서 asyncio.to_thread() 적용
A2A 통합 누락

현재: MCP만 지원
계획: Phase 3.3에서 A2A Basic Integration