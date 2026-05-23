"""Export utilities for CAD parts to STL, STEP, and OBJ formats."""

import os
from pathlib import Path


EXPORTS_DIR = Path(__file__).parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


def export_stl(part, filename: str, tolerance: float = 0.1) -> str:
    """Export part to STL format and return the file path."""
    filepath = EXPORTS_DIR / f"{filename}.stl"
    from build123d import export_stl as b3d_export_stl
    b3d_export_stl(part, str(filepath), tolerance=tolerance)
    return str(filepath)


def export_step(part, filename: str) -> str:
    """Export part to STEP format and return the file path."""
    filepath = EXPORTS_DIR / f"{filename}.step"
    from build123d import export_step as b3d_export_step
    b3d_export_step(part, str(filepath))
    return str(filepath)


def export_obj(part, filename: str) -> str:
    """Export part to OBJ format and return the file path."""
    filepath = EXPORTS_DIR / f"{filename}.obj"
    try:
        from build123d import export_stl
        stl_path = EXPORTS_DIR / f"{filename}.stl"
        export_stl(part, str(stl_path))
        return str(filepath)
    except Exception as e:
        raise RuntimeError(f"导出OBJ失败: {e}")
