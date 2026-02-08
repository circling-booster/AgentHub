"""Settings Override 테스트 (근본 원인 파악)"""

import os

import pytest


class TestSettingsOverride:
    """환경변수 설정이 제대로 동작하는지 검증"""

    @pytest.mark.skipif(
        os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true",
        reason="Dual-Track is disabled in CI environment (no real MCP server)",
    )
    async def test_dual_track_env_var_is_read(self, authenticated_client):
        """MCP__ENABLE_DUAL_TRACK 환경변수가 읽히는지 확인 (로컬 환경만)"""
        # 환경변수 확인
        env_value = os.environ.get("MCP__ENABLE_DUAL_TRACK")
        assert env_value == "true", f"Environment variable not set: {env_value}"

        # Container settings 확인
        container = authenticated_client.app.container
        settings = container.settings()

        assert settings.mcp.enable_dual_track is True, (
            f"settings.mcp.enable_dual_track = {settings.mcp.enable_dual_track}"
        )
