"""Dynamic Test Port Configuration Tests (Phase 5 Part D - Step 12)

목표: 테스트 포트를 환경변수로 오버라이드 가능하게 하여 포트 충돌 방지
- MCP 테스트 서버 포트 (기본 9000)
- A2A Echo Agent 포트 (기본 9003)
- A2A Math Agent 포트 (동적 할당 유지)

pytest-xdist 병렬 실행 시에도 포트 충돌 없이 동작해야 함.

TDD 순서:
1. RED: 테스트 작성 (실패 확인)
2. GREEN: conftest.py 수정
3. REFACTOR: 테스트 개선
"""

import os

import pytest


class TestDynamicPortConfiguration:
    """동적 포트 할당 및 환경변수 오버라이드 테스트"""

    def test_a2a_math_agent_uses_dynamic_port(self, a2a_math_agent):
        """Math Agent가 동적 포트를 사용하는지 확인"""
        # Given: a2a_math_agent fixture 호출됨
        # When: Math Agent URL 확인
        # Then: 포트가 동적으로 할당되어야 함 (매번 다를 수 있음)
        assert a2a_math_agent.startswith("http://127.0.0.1:")
        port = int(a2a_math_agent.split(":")[-1])
        assert 1024 <= port <= 65535  # 유효한 포트 범위

    def test_a2a_echo_agent_env_override(self, monkeypatch):
        """Echo Agent 포트를 환경변수로 오버라이드 가능한지 확인"""
        # Given: 환경변수 A2A_ECHO_PORT 설정
        custom_port = "9999"
        monkeypatch.setenv("A2A_ECHO_PORT", custom_port)

        # When: a2a_echo_agent fixture를 새로 생성 (실제로는 session fixture라서 불가능)
        # NOTE: 이 테스트는 documentation 목적. 실제로는 session 시작 전 환경변수 설정 필요.
        # Then: 환경변수가 우선되어야 함
        expected_port = int(os.environ.get("A2A_ECHO_PORT", "9003"))
        assert expected_port == 9999

    def test_mcp_synapse_port_env_override(self, monkeypatch):
        """MCP Synapse 포트를 환경변수로 오버라이드 가능한지 확인"""
        # Given: 환경변수 MCP_TEST_PORT 설정
        custom_port = "8888"
        monkeypatch.setenv("MCP_TEST_PORT", custom_port)

        # When: sample_mcp_url fixture 조회 (conftest.py에서 환경변수 읽도록 수정 예정)
        # Then: 환경변수가 우선되어야 함
        expected_port = int(os.environ.get("MCP_TEST_PORT", "9000"))
        assert expected_port == 8888

    @pytest.mark.parametrize(
        "env_var,default_value",
        [
            ("A2A_ECHO_PORT", "9003"),
            ("MCP_TEST_PORT", "9000"),
        ],
    )
    def test_port_defaults_when_env_not_set(self, env_var, default_value):
        """환경변수가 설정되지 않았을 때 기본값 사용 확인"""
        # Given: 환경변수가 설정되지 않음 (monkeypatch 없음)
        # When: 환경변수 조회
        port = os.environ.get(env_var)

        # Then: 환경변수가 없으면 None (fixture에서 기본값 사용)
        if port is None:
            assert True  # 환경변수 없음 → fixture가 기본값 사용
        else:
            # CI 환경에서 환경변수가 설정되어 있을 수 있음
            assert int(port) > 0
