# S6-BA-007: Structured JSON logging — all services emit JSON log lines for Loki
import logging
import json
import time
import traceback
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line — Loki/Promtail compatible."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "service": "aakp-api",
        }
        if record.exc_info:
            log_obj["exception"] = traceback.format_exception(*record.exc_info)
        # Attach any extra fields set on the log record
        for key, val in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
            }:
                log_obj[key] = val
        return json.dumps(log_obj, default=str, ensure_ascii=False)


def configure_logging(service_name: str = "aakp-api", level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # Set service name for all records
    logging.getLogger().name = service_name
