"""Natural language prompt engine for CAD generation."""

import re
from typing import Dict, Any, Tuple

from .templates import PART_TEMPLATES, EXAMPLE_PROMPTS


class PromptEngine:
    """Parses natural language prompts into CAD part parameters."""

    def __init__(self):
        self.templates = PART_TEMPLATES
        self.examples = EXAMPLE_PROMPTS

    def process(self, prompt: str) -> Dict[str, Any]:
        """Parse a natural language prompt and return structured params."""
        prompt_lower = prompt.lower()

        # Detect part type
        part_type = self._detect_part_type(prompt_lower)

        # Extract numeric parameters
        params = self._extract_params(prompt_lower, part_type)

        return {
            "type": part_type,
            "params": params,
            "prompt": prompt,
        }

    def _detect_part_type(self, prompt: str) -> str:
        """Detect the type of part from the prompt."""
        bracket_keywords = ["支架", "bracket", "l型", "t型", "角码", "l bracket", "t bracket", "角铁"]
        gear_keywords = ["齿轮", "gear", "齿", "spur", "传动", "齿条"]
        mount_keywords = ["电机", "motor", "马达", "安装板", "mount", "nema"]
        bolt_keywords = ["螺栓", "螺钉", "bolt", "screw"]
        nut_keywords = ["螺母", "nut"]
        washer_keywords = ["垫片", "washer", "垫圈"]
        shaft_keywords = ["轴", "shaft", "光轴", "台阶轴"]
        bearing_keywords = ["轴承", "bearing"]

        for kw in mount_keywords:
            if kw in prompt:
                return "motor_mount"
        for kw in bolt_keywords:
            if kw in prompt:
                return "bolt"
        for kw in nut_keywords:
            if kw in prompt:
                return "nut"
        for kw in washer_keywords:
            if kw in prompt:
                return "washer"
        for kw in bearing_keywords:
            if kw in prompt:
                return "bearing"
        for kw in shaft_keywords:
            if kw in prompt:
                return "shaft"
        for kw in gear_keywords:
            if kw in prompt:
                return "gear"
        for kw in bracket_keywords:
            if kw in prompt:
                return "bracket"

        return "bracket"

    def _extract_params(self, prompt: str, part_type: str) -> Dict[str, Any]:
        """Extract numeric parameters from the prompt."""
        params = {}

        # Generic number extraction
        numbers = re.findall(r"(\d+(?:\.\d+)?)", prompt)

        if part_type == "bracket":
            params = self._extract_bracket_params(prompt, numbers)
        elif part_type == "gear":
            params = self._extract_gear_params(prompt, numbers)
        elif part_type == "motor_mount":
            params = self._extract_motor_mount_params(prompt, numbers)
        elif part_type == "bolt":
            params = self._extract_bolt_params(prompt, numbers)
        elif part_type == "nut":
            params = self._extract_nut_params(prompt, numbers)
        elif part_type == "washer":
            params = self._extract_washer_params(prompt, numbers)
        elif part_type == "shaft":
            params = self._extract_shaft_params(prompt, numbers)
        elif part_type == "bearing":
            params = self._extract_bearing_params(prompt, numbers)

        return params

    def _extract_bracket_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["bracket"]

        # Look for length/width/height keywords
        length_match = re.search(r"长[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        width_match = re.search(r"宽[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        height_match = re.search(r"高[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        thickness_match = re.search(r"厚[度为是:：]*(\d+(?:\.\d+)?)", prompt)

        if length_match:
            params["length"] = float(length_match.group(1))
        if width_match:
            params["width"] = float(width_match.group(1))
        if height_match:
            params["height"] = float(height_match.group(1))
        if thickness_match:
            params["thickness"] = float(thickness_match.group(1))

        # Hole detection
        hole_match = re.search(r"(\d+)\s*[个x]?\s*[mM]?(\d+(?:\.\d+)?)\s*[孔洞]", prompt)
        if hole_match:
            params["hole_count"] = int(hole_match.group(1))
            params["hole_diameter"] = float(hole_match.group(2))
        elif re.search(r"孔|hole", prompt):
            hole_d_match = re.search(r"[孔洞直径为是:：]*(\d+(?:\.\d+)?)", prompt)
            if hole_d_match:
                params["hole_diameter"] = float(hole_d_match.group(1))

        # M6 detection
        if re.search(r"[mM]6", prompt):
            params["hole_diameter"] = 6.5

        # Fill defaults
        for key, value in default.items():
            params.setdefault(key, value)

        return params

    def _extract_gear_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["gear"]

        module_match = re.search(r"模[数数为是:：]*(\d+(?:\.\d+)?)", prompt)
        teeth_match = re.search(r"(\d+)\s*[个]?(?:齿|tooth|teeth)", prompt)
        width_match = re.search(r"宽[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        bore_match = re.search(r"孔[径为是:：]*(\d+(?:\.\d+)?)", prompt)

        if module_match:
            params["module"] = float(module_match.group(1))
        if teeth_match:
            params["tooth_count"] = int(teeth_match.group(1))
        if width_match:
            params["face_width"] = float(width_match.group(1))
        if bore_match:
            params["bore_diameter"] = float(bore_match.group(1))

        # Detect gear type
        if "斜齿" in prompt or "helical" in prompt:
            params["gear_type"] = "helical"
            helix_match = re.search(r"(\d+)\s*[度°]?\s*(?:螺旋角|helix)", prompt)
            if helix_match:
                params["helix_angle"] = float(helix_match.group(1))
            else:
                params["helix_angle"] = 15.0
        elif "齿条" in prompt or "rack" in prompt:
            params["gear_type"] = "rack"
            length_match = re.search(r"长[度为是:：]*(\d+(?:\.\d+)?)", prompt)
            if length_match:
                params["rack_length"] = float(length_match.group(1))
        else:
            params["gear_type"] = "spur"

        for key, value in default.items():
            params.setdefault(key, value)

        return params

    def _extract_motor_mount_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["motor_mount"]

        length_match = re.search(r"长[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        width_match = re.search(r"宽[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        height_match = re.search(r"高[度为是:：]*(\d+(?:\.\d+)?)", prompt)

        if length_match:
            params["base_length"] = float(length_match.group(1))
        if width_match:
            params["base_width"] = float(width_match.group(1))
        if height_match:
            params["mount_height"] = float(height_match.group(1))

        for key, value in default.items():
            params.setdefault(key, value)

        return params

    def _extract_bolt_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["bolt"]
        d_match = re.search(r"[mM](\d+)", prompt)
        l_match = re.search(r"长[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        if d_match:
            params["diameter"] = float(d_match.group(1))
        if l_match:
            params["length"] = float(l_match.group(1))
        if "内六角" in prompt or "socket" in prompt:
            params["head_type"] = "socket"
        elif "沉头" in prompt or "flat" in prompt:
            params["head_type"] = "flat"
        else:
            params["head_type"] = "hex"
        for key, value in default.items():
            params.setdefault(key, value)
        return params

    def _extract_nut_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["nut"]
        d_match = re.search(r"[mM](\d+)", prompt)
        if d_match:
            params["diameter"] = float(d_match.group(1))
        if "法兰" in prompt or "flange" in prompt:
            params["nut_type"] = "flange"
        elif "锁紧" in prompt or "nylock" in prompt:
            params["nut_type"] = "nylock"
        else:
            params["nut_type"] = "hex"
        for key, value in default.items():
            params.setdefault(key, value)
        return params

    def _extract_washer_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["washer"]
        d_match = re.search(r"[mM](\d+)", prompt)
        if d_match:
            params["inner_diameter"] = float(d_match.group(1)) + 0.5
        if "弹簧" in prompt or "spring" in prompt:
            params["washer_type"] = "spring"
        elif "锁紧" in prompt or "lock" in prompt:
            params["washer_type"] = "lock"
        else:
            params["washer_type"] = "flat"
        for key, value in default.items():
            params.setdefault(key, value)
        return params

    def _extract_shaft_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["shaft"]
        d_match = re.search(r"直[径为是:：]*(\d+(?:\.\d+)?)", prompt)
        l_match = re.search(r"长[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        if d_match:
            params["diameter"] = float(d_match.group(1))
        if l_match:
            params["length"] = float(l_match.group(1))
        if "键槽" in prompt or "keyed" in prompt:
            params["shaft_type"] = "keyed"
        elif "台阶" in prompt or "stepped" in prompt:
            params["shaft_type"] = "stepped"
        elif "螺纹" in prompt or "threaded" in prompt:
            params["shaft_type"] = "threaded"
        else:
            params["shaft_type"] = "round"
        for key, value in default.items():
            params.setdefault(key, value)
        return params

    def _extract_bearing_params(self, prompt: str, numbers: list) -> Dict[str, Any]:
        params = {}
        default = self.templates["bearing"]
        d_match = re.search(r"(?:内[径径]|轴[径径])[为是:：]*(\d+(?:\.\d+)?)", prompt)
        od_match = re.search(r"外[径径为是:：]*(\d+(?:\.\d+)?)", prompt)
        w_match = re.search(r"(?:宽[度为是:：]|厚度[为是:：]*)(\d+(?:\.\d+)?)", prompt)
        series_match = re.search(r"(6\d{3})", prompt)
        if d_match:
            params["inner_diameter"] = float(d_match.group(1))
        if od_match:
            params["outer_diameter"] = float(od_match.group(1))
        if w_match:
            params["width"] = float(w_match.group(1))
        if series_match:
            params["series"] = series_match.group(1)
        if "法兰" in prompt or "flange" in prompt:
            params["bearing_type"] = "flanged"
        elif "推力" in prompt or "thrust" in prompt:
            params["bearing_type"] = "thrust"
        else:
            params["bearing_type"] = "deep_groove"
        for key, value in default.items():
            params.setdefault(key, value)
        return params

    def validate_params(self, parsed: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate parsed parameters."""
        valid_types = ["bracket", "gear", "motor_mount", "bolt", "nut", "washer", "shaft", "bearing"]
        if parsed["type"] not in valid_types:
            return False, f"不支持的零件类型: {parsed['type']}"

        params = parsed["params"]

        if parsed["type"] == "bracket":
            if params.get("length", 0) <= 0:
                return False, "支架长度必须大于0"
            if params.get("thickness", 0) <= 0:
                return False, "支架厚度必须大于0"

        elif parsed["type"] == "gear":
            if params.get("module", 0) <= 0:
                return False, "齿轮模数必须大于0"
            if params.get("tooth_count", 0) < 6:
                return False, "齿轮齿数必须至少为6"

        elif parsed["type"] == "motor_mount":
            if params.get("base_length", 0) <= 0:
                return False, "安装板长度必须大于0"

        elif parsed["type"] == "bolt":
            if params.get("diameter", 0) <= 0:
                return False, "螺栓直径必须大于0"

        elif parsed["type"] == "shaft":
            if params.get("diameter", 0) <= 0:
                return False, "轴直径必须大于0"

        elif parsed["type"] == "bearing":
            if params.get("inner_diameter", 0) <= 0:
                return False, "轴承内径必须大于0"

        return True, "参数验证通过"
