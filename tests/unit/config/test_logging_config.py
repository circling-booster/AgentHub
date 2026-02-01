"""Logging Configuration Tests (TDD RED - Step 7)

Phase 4 Part B: Structured Logging Improvements
"""

import json
import logging
from io import StringIO


def test_json_formatter_creates_valid_json():
    """JSON 포맷터가 유효한 JSON 문자열을 생성해야 함"""
    # Given: JSON 포맷터와 로거
    from src.config.logging_config import JsonFormatter

    formatter = JsonFormatter()
    logger = logging.getLogger("test.json")
    logger.setLevel(logging.INFO)

    # StringIO로 로그 캡처
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # When: 로그 메시지 생성
    logger.info("Test message", extra={"user_id": "123", "action": "login"})

    # Then: 유효한 JSON 파싱 가능
    output = stream.getvalue()
    parsed = json.loads(output.strip())

    assert parsed["message"] == "Test message"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.json"
    assert "timestamp" in parsed
    assert parsed["user_id"] == "123"
    assert parsed["action"] == "login"

    # Cleanup
    logger.removeHandler(handler)


def test_json_formatter_handles_exception_info():
    """JSON 포맷터가 예외 정보를 포함해야 함"""
    # Given: JSON 포맷터
    from src.config.logging_config import JsonFormatter

    formatter = JsonFormatter()
    logger = logging.getLogger("test.exception")
    logger.setLevel(logging.ERROR)

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # When: 예외 로깅
    try:
        raise ValueError("Test error")
    except ValueError:
        logger.exception("Error occurred")

    # Then: exc_info 필드 존재
    output = stream.getvalue()
    parsed = json.loads(output.strip())

    assert parsed["message"] == "Error occurred"
    assert parsed["level"] == "ERROR"
    assert "exc_info" in parsed
    assert "ValueError: Test error" in parsed["exc_info"]

    # Cleanup
    logger.removeHandler(handler)


def test_setup_logging_with_text_format():
    """setup_logging()이 text 포맷으로 로거를 설정해야 함"""
    # Given: 설정 객체
    from src.config.logging_config import setup_logging
    from src.config.settings import Settings

    settings = Settings()
    settings.observability.log_format = "text"

    # When: 로깅 설정
    setup_logging(settings)

    # Then: 루트 로거 핸들러 확인
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0

    # 포맷터가 JSON이 아닌 일반 텍스트여야 함
    handler = root_logger.handlers[0]
    from src.config.logging_config import JsonFormatter

    assert not isinstance(handler.formatter, JsonFormatter)


def test_setup_logging_with_json_format():
    """setup_logging()이 json 포맷으로 로거를 설정해야 함"""
    # Given: 설정 객체
    from src.config.logging_config import setup_logging
    from src.config.settings import Settings

    settings = Settings()
    settings.observability.log_format = "json"

    # When: 로깅 설정
    setup_logging(settings)

    # Then: 루트 로거 핸들러가 JsonFormatter 사용
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0

    handler = root_logger.handlers[0]
    from src.config.logging_config import JsonFormatter

    assert isinstance(handler.formatter, JsonFormatter)
