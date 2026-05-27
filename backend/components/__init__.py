"""Components module - 机械标准件生态库。"""

from .shafts import Shaft, ShaftParams, get_shaft_fit, get_bearing_fit, get_gear_fit
from .bearings import Bearing, BearingParams
from .gears import Gear, GearParams, calculate_center_distance, calculate_gear_ratio, auto_select_gears, calculate_mesh_position
