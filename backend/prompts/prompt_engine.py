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
        gear_keywords = ["齿轮", "gear", "齿", "spur", "传动"]
        mount_keywords = ["电机", "motor", "马达", "安装板", "mount", "nema"]

        for kw in mount_keywords:
            if kw in prompt:
                return "motor_mount"

        for kw in gear_keywords:
            if kw in prompt:
                return "gear"

        for kw in bracket_keywords:
            if kw in prompt:
                return "bracket"

        # Default to bracket
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
        teeth_match = re.search(r"(\d+)\s*[个齿|齿]", prompt)
        width_match = re.search(r"宽[度为是:：]*(\d+(?:\.\d+)?)", prompt)
        bore_match = re.search(r"孔[径为是:：]*(\d+(?:\.\d+)?)", prompt)

        if module_match:
            params["module"] = float(module_match.group(1))
        if teeth_match:
            params["teeth_count"] = int(teeth_match.group(1))
        if width_match:
            params["width"] = float(width_match.group(1))
        if bore_match:
            params["bore_diameter"] = float(bore_match.group(1))

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

    def validate_params(self, parsed: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate parsed parameters."""
        if parsed["type"] not in ["bracket", "gear", "motor_mount"]:
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
            if params.get("teeth_count", 0) < 6:
                return False, "齿轮齿数必须至少为6"

        elif parsed["type"] == "motor_mount":
            if params.get("base_length", 0) <= 0:
                return False, "安装板长度必须大于0"

        return True, "参数验证通过"
