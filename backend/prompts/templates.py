"""Prompt templates and example prompts."""

PART_TEMPLATES = {
    "bracket": {
        "length": 80,
        "width": 40,
        "height": 60,
        "thickness": 5,
        "hole_diameter": 6.5,
        "hole_count": 4,
        "fillet_radius": 2.0,
    },
    "gear": {
        "module": 2,
        "tooth_count": 20,
        "face_width": 10,
        "bore_diameter": 8,
        "pressure_angle": 20.0,
        "gear_type": "spur",
        "helix_angle": 0,
        "rack_length": 100,
    },
    "motor_mount": {
        "base_length": 60,
        "base_width": 60,
        "base_thickness": 5,
        "mount_height": 40,
    },
    "bolt": {
        "diameter": 6,
        "length": 20,
        "head_type": "hex",
    },
    "nut": {
        "diameter": 6,
        "nut_type": "hex",
    },
    "washer": {
        "inner_diameter": 6.5,
        "outer_diameter": 12,
        "washer_type": "flat",
    },
    "shaft": {
        "diameter": 8,
        "length": 120,
        "shaft_type": "round",
    },
    "bearing": {
        "inner_diameter": 8,
        "outer_diameter": 22,
        "width": 7,
        "bearing_type": "deep_groove",
    },
}

EXAMPLE_PROMPTS = [
    "生成一个带4个M6孔的L型支架",
    "创建一个模数2、20齿的直齿轮",
    "做一个NEMA17电机安装板",
    "生成一个100x50的T型支架，厚度5mm",
    "创建一个模数3、30齿、宽度15mm的齿轮",
    "生成一个80x80的电机安装板，高度50mm",
    "做一个15度螺旋角的斜齿轮",
    "生成一个模数2、长度100的齿条",
    "生成M6六角螺栓，长度20mm",
    "设计一个直径8mm的键槽轴",
]
