"""Logging Configuration

Phase 4 Part B Step 7: Structured Logging Improvements
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings


class JsonFormatter(logging.Formatter):
    """JSON 포맷 로거

    로그를 JSON 형태로 출력하여 구조화된 로깅을 지원합니다.
    외부 로그 수집 시스템(예: ELK, Datadog)과 통합 시 유용합니다.
    """

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 문자열로 변환

        Args:
            record: 로그 레코드

        Returns:
            JSON 형태의 로그 문자열
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # extra 필드 추가 (logger.info("msg", extra={...}) 형태)
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "taskName",
            ]:
                log_data[key] = value

        # 예외 정보 추가
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(settings: "Settings") -> None:
    """로깅 설정 초기화

    Args:
        settings: 애플리케이션 설정 객체
    """
    root_logger = logging.getLogger()

    # 기존 핸들러 제거 (중복 방지)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 포맷 설정
    log_format = getattr(settings.observability, "log_format", "text")

    if log_format == "json":
        formatter = JsonFormatter()
    else:
        # 기본 텍스트 포맷
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)
