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
        "teeth_count": 20,
        "width": 10,
        "bore_diameter": 8,
        "pressure_angle": 20.0,
    },
    "motor_mount": {
        "base_length": 60,
        "base_width": 60,
        "base_thickness": 5,
        "mount_height": 40,
    },
}

EXAMPLE_PROMPTS = [
    "生成一个带4个M6孔的L型支架",
    "创建一个模数2、20齿的齿轮",
    "做一个NEMA17电机安装板",
    "生成一个100x50的T型支架，厚度5mm",
    "创建一个模数3、30齿、宽度15mm的齿轮",
    "生成一个80x80的电机安装板，高度50mm",
]
