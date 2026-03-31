"""커스텀 로거 모듈."""

import logging


def get_logger(name: str) -> logging.Logger:
    """커스텀 로거를 생성하여 반환.

    레벨: INFO
    포맷: 접두사 | 시간 | 메시지
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    # [JANGJIWON] : 로그 접두사
    # %(asctime)s : 시간
    # %(message)s : 로그 메시지
    formatter = logging.Formatter(
        "[JANGJIWON] %(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
