"""Utility to generate a simple gating system for casting simulations.

This script models a vertical pouring cup connected to a horizontal runner
and a downward feed channel using ``trimesh`` primitives.  The default
dimensions are taken from the user request:

* Pouring cup diameter: 136.07 mm
* Pouring cup height: 78.00 mm
* Runner length: 112.59 mm
* Feed channel (downstream) length: 162.35 mm
* Runner / feed channel diameter: 20 mm

The resulting mesh can be exported to STL/OBJ/etc. by supplying an output
filename via the ``--export`` argument.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional

import trimesh
from math import pi


@dataclass
class GatingSystemParameters:
    """Geometric parameters for the gating system."""

    cup_diameter: float = 136.07
    cup_height: float = 78.0
    runner_length: float = 112.59
    runner_diameter: float = 20.0
    feed_length: float = 162.35
    feed_diameter: float = 20.0
    runner_center_height: Optional[float] = None

    def resolved_runner_center_height(self) -> float:
        """Return the z position for the runner center.

        If the user does not explicitly specify a center height we align the
        runner tangentially with the bottom of the pouring cup so that the
        runner rests on the base plane.
        """

        if self.runner_center_height is not None:
            return self.runner_center_height
        return self.runner_diameter / 2.0


def _create_pouring_cup(params: GatingSystemParameters) -> trimesh.Trimesh:
    cup = trimesh.creation.cylinder(
        radius=params.cup_diameter / 2.0,
        height=params.cup_height,
        sections=64,
    )
    # Move the cup so that its base is on the global XY plane.
    cup.apply_translation((0.0, 0.0, params.cup_height / 2.0))
    return cup


def _create_runner(params: GatingSystemParameters) -> trimesh.Trimesh:
    runner = trimesh.creation.cylinder(
        radius=params.runner_diameter / 2.0,
        height=params.runner_length,
        sections=64,
    )
    # Align the cylinder with the X axis.
    rotation = trimesh.transformations.rotation_matrix(pi / 2.0, (0.0, 1.0, 0.0))
    runner.apply_transform(rotation)
    runner_center_height = params.resolved_runner_center_height()
    # Position the runner so that it starts at the origin and extends along +X.
    runner.apply_translation((params.runner_length / 2.0, 0.0, runner_center_height))
    return runner


def _create_feed_channel(params: GatingSystemParameters) -> trimesh.Trimesh:
    feed = trimesh.creation.cylinder(
        radius=params.feed_diameter / 2.0,
        height=params.feed_length,
        sections=64,
    )
    runner_center_height = params.resolved_runner_center_height()
    # Attach the feed channel to the end of the runner and extend downward.
    feed.apply_translation(
        (
            params.runner_length,
            0.0,
            runner_center_height - params.feed_length / 2.0,
        )
    )
    return feed


def build_gating_system_mesh(params: GatingSystemParameters) -> trimesh.Trimesh:
    """Create a combined mesh representing the gating system."""

    components = (
        _create_pouring_cup(params),
        _create_runner(params),
        _create_feed_channel(params),
    )
    return trimesh.util.concatenate(components)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cup-diameter", type=float, default=136.07)
    parser.add_argument("--cup-height", type=float, default=78.0)
    parser.add_argument("--runner-length", type=float, default=112.59)
    parser.add_argument("--runner-diameter", type=float, default=20.0)
    parser.add_argument("--feed-length", type=float, default=162.35)
    parser.add_argument("--feed-diameter", type=float, default=20.0)
    parser.add_argument(
        "--runner-center-height",
        type=float,
        default=None,
        help=(
            "Optional z-height for the runner center. If omitted the runner "
            "touches the build plate."
        ),
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Optional path to export the generated mesh (e.g. output.stl).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = GatingSystemParameters(
        cup_diameter=args.cup_diameter,
        cup_height=args.cup_height,
        runner_length=args.runner_length,
        runner_diameter=args.runner_diameter,
        feed_length=args.feed_length,
        feed_diameter=args.feed_diameter,
        runner_center_height=args.runner_center_height,
    )

    mesh = build_gating_system_mesh(params)

    if args.export:
        mesh.export(args.export)
        print(f"Exported gating system mesh to {args.export}")

    extents = mesh.extents
    print(
        "Bounding box (mm): width={:.2f}, depth={:.2f}, height={:.2f}".format(
            extents[0], extents[1], extents[2]
        )
    )


if __name__ == "__main__":
    main()
