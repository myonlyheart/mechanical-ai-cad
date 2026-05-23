"""Hole utility functions for CAD parts."""

from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle,
    extrude, Location, Vector, Rotation, Mode,
)


def add_hole(part, location, diameter, depth, mode=Mode.SUBTRACT):
    """Add a through hole at the specified location."""
    with BuildPart(part, mode=mode) as hole:
        with BuildSketch(Location(location)) as hs:
            Circle(diameter / 2)
        extrude(amount=depth, mode=mode)
    return part


def add_counterbore(part, location, hole_diameter, cb_diameter, cb_depth, total_depth):
    """Add a counterbore hole."""
    with BuildPart(part, mode=Mode.SUBTRACT) as cb:
        # Through hole
        with BuildSketch(Location(location)) as hs1:
            Circle(hole_diameter / 2)
        extrude(amount=total_depth, mode=Mode.SUBTRACT)

        # Counterbore
        with BuildSketch(Location(location)) as hs2:
            Circle(cb_diameter / 2)
        extrude(amount=cb_depth, mode=Mode.SUBTRACT)
    return part


def add_countersink(part, location, hole_diameter, cs_diameter, total_depth):
    """Add a countersink hole."""
    with BuildPart(part, mode=Mode.SUBTRACT) as cs:
        with BuildSketch(Location(location)) as hs:
            Circle(hole_diameter / 2)
        extrude(amount=total_depth, mode=Mode.SUBTRACT)
    return part


def add_slot(part, location, width, length, depth, mode=Mode.SUBTRACT):
    """Add a slot feature using a rectangle."""
    with BuildPart(part, mode=mode) as slot:
        with BuildSketch(Location(location)) as ss:
            Rectangle(width, length)
        extrude(amount=depth, mode=mode)
    return part


def add_pattern_holes(part, location, diameter, depth, count, spacing_x, spacing_y):
    """Add a pattern of holes."""
    for i in range(count):
        x = location[0] + i * spacing_x
        y = location[1] + i * spacing_y
        add_hole(part, (x, y, location[2]), diameter, depth)
    return part
