"""Hole utility functions for CAD parts."""

from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle,
    extrude, Location, Pos, Mode,
)


def add_hole(part_obj, center, diameter, depth):
    """Add a through hole."""
    with BuildPart(part_obj, mode=Mode.SUBTRACT):
        with BuildSketch(Location(center)):
            Circle(diameter / 2)
        extrude(amount=depth, both=True)
    return part_obj


def add_counterbore(part_obj, center, hole_d, cb_d, cb_depth, total_depth):
    """Add a counterbore hole."""
    with BuildPart(part_obj, mode=Mode.SUBTRACT):
        with BuildSketch(Location(center)):
            Circle(hole_d / 2)
        extrude(amount=total_depth, both=True)
    with BuildPart(part_obj, mode=Mode.SUBTRACT):
        with BuildSketch(Location(center)):
            Circle(cb_d / 2)
        extrude(amount=cb_depth)
    return part_obj


def add_countersink(part_obj, center, hole_d, total_depth):
    """Add a countersink hole."""
    with BuildPart(part_obj, mode=Mode.SUBTRACT):
        with BuildSketch(Location(center)):
            Circle(hole_d / 2)
        extrude(amount=total_depth, both=True)
    return part_obj


def add_slot(part_obj, center, width, length, depth):
    """Add a rectangular slot."""
    with BuildPart(part_obj, mode=Mode.SUBTRACT):
        with BuildSketch(Location(center)):
            Rectangle(width, length)
        extrude(amount=depth, both=True)
    return part_obj


def add_pattern_holes(part_obj, center, diameter, depth, count, spacing_x, spacing_y):
    """Add a pattern of holes."""
    for i in range(count):
        x = center[0] + i * spacing_x
        y = center[1] + i * spacing_y
        add_hole(part_obj, (x, y, center[2]), diameter, depth)
    return part_obj
