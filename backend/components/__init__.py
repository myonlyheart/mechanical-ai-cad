"""Components module - 机械标准件生态库。"""

from .shafts import Shaft, ShaftParams, get_shaft_fit, get_bearing_fit, get_gear_fit
from .bearings import Bearing, BearingParams
from .gears import Gear, GearParams, calculate_center_distance, calculate_gear_ratio, auto_select_gears, calculate_mesh_position
from .motors import MotorSpec, get_motor_spec, list_motors, recommend_coupling, get_mount_params
from .rails import LinearRailSpec, LeadScrewSpec, get_rail_spec, get_screw_spec, list_rails, list_screws, calculate_travel, calculate_steps_per_mm
