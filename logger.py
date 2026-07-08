"""
공통 로거.

- 콘솔 + 로테이팅 파일(logs/canon_smb_auto.log)에 동시 기록
- 로그에 비밀번호가 실수로 찍히지 않도록 마스킹 필터 포함
- GUI 로그창에 실시간으로 흘려보낼 수 있도록 콜백 핸들러 지원
"""

import logging
import logging.handlers
import os
import re

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "canon_smb_auto.log")

_PW_PATTERN = re.compile(r"(pw|password|pwd)\s*[:=]\s*\S+", re.IGNORECASE)


class MaskSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _PW_PATTERN.sub(r"\1=******", record.msg)
        return True


class QtSignalHandler(logging.Handler):
    """GUI 쪽 QThread에서 emit(text)로 로그를 화면에 뿌리기 위한 핸들러."""

    def __init__(self, emit_func):
        super().__init__()
        self.emit_func = emit_func

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.emit_func(msg)
        except Exception:
            pass


def get_logger(name: str = "canon_smb_auto") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 이미 설정됨

    os.makedirs(LOG_DIR, exist_ok=True)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    console.addFilter(MaskSecretsFilter())

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    file_handler.addFilter(MaskSecretsFilter())

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
