"""Chaos Engineering Test Fixtures

Chaos 테스트용 fixtures:
- chaotic_mcp_server: 랜덤 타이밍에 종료 가능한 MCP 서버
- 돌발 실패, Rate Limit, 동시성 시나리오 시뮬레이션

환경변수:
- MCP_CHAOS_PORT: Chaos 테스트용 MCP 서버 포트 (기본 9999)
  일반 테스트 포트(9000~9002)와 구분하여 독립 실행
"""

import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest


@pytest.fixture
async def chaotic_mcp_server() -> AsyncIterator[tuple[str, subprocess.Popen]]:
    """
    랜덤 타이밍에 종료되는 MCP 서버

    환경변수:
        MCP_CHAOS_PORT: Chaos 테스트 전용 포트 (기본 9999, 일반 MCP와 독립)

    Yields:
        tuple[str, Popen]: (서버 URL, 프로세스 객체)
        - URL을 사용해 테스트 중 도구 호출
        - Popen을 사용해 테스트 중 서버 강제 종료

    Example:
        @pytest.mark.chaos
        @pytest.mark.local_mcp
        async def test_mcp_failure(chaotic_mcp_server):
            url, proc = chaotic_mcp_server
            # ... 도구 호출 ...
            proc.terminate()  # 강제 종료
            # Circuit Breaker 동작 검증
    """
    # CI 환경에서는 skip (Mock 사용 불가, 실제 프로세스 제어 필요)
    if os.getenv("CI") == "true":
        pytest.skip("Chaos tests require real subprocess, skipped in CI")

    # MCP 서버 경로
    mcp_server_path = Path.home() / "Documents" / "GitHub" / "MCP_SERVER" / "MCP_Streamable_HTTP"

    if not mcp_server_path.exists():
        pytest.skip(f"MCP server not found: {mcp_server_path}")

    # Chaos 테스트용 독립 포트 (일반 MCP 테스트 9000~9002와 충돌 방지)
    chaos_port = int(os.getenv("MCP_CHAOS_PORT", "9999"))
    env = os.environ.copy()
    env["SYNAPSE_PORT"] = str(chaos_port)

    # MCP 서버 시작
    proc = subprocess.Popen(
        [sys.executable, "-m", "synapse"],
        cwd=str(mcp_server_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 서버 시작 대기 (최대 5초)
    started = False
    for _ in range(10):
        await asyncio.sleep(0.5)
        if proc.poll() is None:  # 프로세스가 살아있는지 확인
            started = True
            break

    if not started:
        # 시작 실패 시 stderr 출력
        _, stderr = proc.communicate(timeout=1)
        pytest.fail(f"Chaotic MCP server failed to start: {stderr.decode()}")

    url = f"http://127.0.0.1:{chaos_port}/mcp"

    try:
        yield url, proc
    finally:
        # Cleanup: 서버 종료
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


@pytest.fixture
def chaos_retry_config() -> dict:
    """
    Chaos 테스트용 재시도 설정

    짧은 타임아웃과 적은 재시도 횟수로 테스트 속도 향상
    """
    return {
        "max_retries": 3,
        "retry_backoff_seconds": 0.1,  # 100ms (테스트 가속)
        "timeout_seconds": 2,  # 2초 (기본 120초보다 짧게)
    }


# Integration fixtures 재사용 (temp_data_dir)
# pytest_plugins는 top-level conftest에서만 허용되므로 직접 정의


@pytest.fixture
def temp_data_dir() -> Path:
    """임시 데이터 디렉토리 생성"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def container(temp_data_dir: Path):
    """
    Chaos 테스트용 DI Container

    authenticated_client 대신 직접 container를 사용하는 테스트를 위한 fixture
    (예: GatewayService, RegistryService 직접 접근)
    """
    from src.adapters.inbound.http.app import create_app

    # FastAPI 앱 생성
    app = create_app()
    container = app.container

    # Container 재설정 (임시 데이터 디렉토리)
    container.reset_singletons()
    container.settings().storage.data_dir = str(temp_data_dir)
    container.settings().llm.default_model = "openai/gpt-4o-mini"

    # Storage 오버라이드 (temp_data_dir 사용)
    from dependency_injector import providers

    from src.adapters.outbound.storage.sqlite_conversation_storage import (
        SqliteConversationStorage,
    )
    from src.adapters.outbound.storage.sqlite_usage import SqliteUsageStorage

    conv_db_path = str(temp_data_dir / "agenthub.db")
    usage_db_path = str(temp_data_dir / "usage.db")

    container.conversation_storage.override(
        providers.Singleton(SqliteConversationStorage, db_path=conv_db_path)
    )
    container.usage_storage.override(providers.Singleton(SqliteUsageStorage, db_path=usage_db_path))

    # 초기화
    conv_storage = container.conversation_storage()
    usage_storage = container.usage_storage()
    orchestrator = container.orchestrator_adapter()

    await conv_storage.initialize()
    await usage_storage.initialize()
    await orchestrator.initialize()

    yield container

    # Cleanup
    await conv_storage.close()
    await usage_storage.close()
    await orchestrator.close()
    container.conversation_storage.reset_override()
    container.usage_storage.reset_override()
    container.reset_singletons()
    container.unwire()
