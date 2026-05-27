"""Motors - 电机系统。"""

from .motor_specs import (
    MotorSpec, MOTOR_SPECS,
    get_motor_spec, list_motors,
    recommend_coupling, get_mount_params,
)

__all__ = [
    "MotorSpec", "MOTOR_SPECS",
    "get_motor_spec", "list_motors",
    "recommend_coupling", "get_mount_params",
]
