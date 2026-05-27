"""日志系统 - 记录工程操作日志。

记录项：
- constraint solve（约束求解）
- repair（修复操作）
- validation（校验结果）
- assembly updates（装配更新）
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# 日志目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def _setup_logger(name: str, filename: str) -> logging.Logger:
    """设置日志记录器。"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # 文件处理器
        fh = logging.FileHandler(LOG_DIR / filename, encoding="utf-8")
        fh.setLevel(logging.INFO)

        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


# 各模块日志器
constraint_logger = _setup_logger("constraint", "constraint.log")
repair_logger = _setup_logger("repair", "repair.log")
validation_logger = _setup_logger("validation", "validation.log")
assembly_logger = _setup_logger("assembly", "assembly.log")
general_logger = _setup_logger("general", "general.log")


def log_constraint_solve(
    part_type: str, params: dict[str, Any], result: dict[str, Any],
) -> None:
    """记录约束求解。"""
    constraint_logger.info(
        f"SOLVE | type={part_type} | valid={result.get('valid')} | "
        f"fixes={len(result.get('fixes_applied', []))}"
    )


def log_repair(
    part_type: str, original: dict[str, Any], repaired: dict[str, Any],
    fixes: list[str],
) -> None:
    """记录修复操作。"""
    repair_logger.info(
        f"REPAIR | type={part_type} | fixes={len(fixes)} | "
        f"details={json.dumps(fixes, ensure_ascii=False)}"
    )


def log_validation(
    check_type: str, valid: bool, issues: list[dict[str, Any]],
) -> None:
    """记录校验结果。"""
    error_count = sum(1 for i in issues if i.get("severity") == "error")
    validation_logger.info(
        f"VALIDATE | check={check_type} | valid={valid} | errors={error_count}"
    )


def log_assembly_update(
    assembly_name: str, action: str, details: str = "",
) -> None:
    """记录装配更新。"""
    assembly_logger.info(
        f"ASSEMBLY | name={assembly_name} | action={action} | {details}"
    )


def log_api_request(
    method: str, path: str, status: int, duration_ms: float,
) -> None:
    """记录 API 请求。"""
    general_logger.info(
        f"API | {method} {path} | status={status} | duration={duration_ms:.1f}ms"
    )
