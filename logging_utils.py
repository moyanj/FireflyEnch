"""FireflyEnch 日志工具。"""

import logging
import os
import sys
from urllib.parse import urlsplit, urlunsplit

from loguru import logger


class InterceptHandler(logging.Handler):
    """把标准 logging 转发到 loguru。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(
    level: str,
    log_path: str | None = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """配置控制台、文件与标准 logging 转发。"""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level:<8}</level> | "
            "{message}"
        ),
    )

    if log_path:
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        logger.add(
            log_path,
            level=level.upper(),
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            backtrace=False,
            diagnose=False,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}",
        )

    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

    for name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "tortoise",
        "aiomysql",
        "asyncio",
    ):
        target = logging.getLogger(name)
        target.handlers = [intercept_handler]
        target.propagate = False


def mask_db_connection(connection: str) -> str:
    """对数据库连接串中的密码做脱敏。"""
    if "://" not in connection or "@" not in connection:
        return connection

    parsed = urlsplit(connection)
    if parsed.password is None:
        return connection

    auth = parsed.username or ""
    if auth:
        auth = f"{auth}:***"
    else:
        auth = "***"

    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"

    netloc = f"{auth}@{host}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def build_startup_log_context(
    *,
    app_name: str,
    app_port: int,
    data_path: str,
    upload_folder: str,
    thumbnail_folder: str,
    temp_upload_folder: str,
    db_type: str,
    db_connection: str,
    ai_enabled: bool,
    log_level: str,
    log_path: str,
) -> dict[str, str | int | bool]:
    """构建启动日志摘要。"""
    return {
        "应用名": app_name,
        "端口": app_port,
        "数据目录": data_path,
        "上传目录": upload_folder,
        "缩略图目录": thumbnail_folder,
        "临时目录": temp_upload_folder,
        "数据库类型": db_type,
        "数据库连接": mask_db_connection(db_connection),
        "AI启用": ai_enabled,
        "日志级别": log_level.upper(),
        "日志文件": log_path,
    }
