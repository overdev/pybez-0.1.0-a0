# -*- encoding: utf8 -*-
# ------------------------------------------------------------------------------
# api.py
# Created on 16/10/2021
#
# The MIT License
#
#
# Copyright 2021 Jorge A. Gomes
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------

# region IMPORTS
import math
import sys
from enum import Enum, auto

from typing import Optional, Any, Union, List, Tuple, Sequence

# endregion (imports)
# ---------------------------------------------------------
# region EXPORTS


__all__ = [
    'Number',
    'Vec2',

    'BezierMode',
    'BM_QUADRATIC',
    'BM_CUBIC',

    'PointMode',
    'PM_CUSP',
    'PM_SMOOTH',
    'PM_SYMMETRICAL',

    'PointType',
    'PT_POSITION',
    'PT_CTRL_BEGIN',
    'PT_CTRL_END',

    'Point',
    'Bezier',

    'cubic',
    'quadratic',
]


# endregion (exports)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS

Number = Union[int, float]
Vec2 = Union[Sequence[Number], Tuple[Number, Number], List[Number]]


class BezierMode(Enum):
    """BezierMode enumeration

    Defines the types of bezier curve supported.
    """
    QUADRATIC = 0
    CUBIC = auto()


BM_QUADRATIC = BezierMode.QUADRATIC
BM_CUBIC = BezierMode.CUBIC


class PointMode(Enum):
    """PointMode enumeration

    Defines how the control points behave when moved
    """
    CUSP = 0
    SMOOTH = auto()
    SYMMETRICAL = auto()


PM_CUSP = PointMode.CUSP
PM_SMOOTH = PointMode.SMOOTH
PM_SYMMETRICAL = PointMode.SYMMETRICAL


class PointType(Enum):
    """PointType enumeration

    Defines the type of each vector in a bezier point
    """
    POSITION = 0
    CTRL_BEGIN = auto()
    CTRL_END = auto()


PT_POSITION = PointType.POSITION
PT_CTRL_BEGIN = PointType.CTRL_BEGIN
PT_CTRL_END = PointType.CTRL_END


# endregion (constants)
# ---------------------------------------------------------
# region CLASSES


class Point:

    __slots__ = 'pos', 'begin', 'end', 'mode'

    def __init__(self, x: Number = 0, y: Number = 0, dist: Number = 10):
        self.pos: Vec2 = [x, y]
        self.begin: Vec2 = [x + dist, y]
        self.end: Vec2 = [x - dist, y]
        self.mode: PointMode = PM_SYMMETRICAL

    def __getitem__(self, key):
        return self.pos.__getitem__(key)

    def __setitem__(self, key, value):
        return self.pos.__getitem__(key, value)

    def find_point(self, location: Vec2, margin: int = 2) -> Optional[Tuple[PointType, Vec2]]:
        for i, p in enumerate((self.pos, self.begin, self.end)):
            x, y = location
            px, py = p
            ox = x - px
            oy = y - py

            if abs(ox) > margin or abs(oy) > margin:
                continue
            return (PT_POSITION, PT_CTRL_BEGIN, PT_CTRL_END)[i], [ox, oy]
        return None

    def move_point(self, point_type: PointType, position: Vec2, offset: Vec2 = (0, 0)):
        x, y = position
        ox, oy = offset
        px, py = self.pos
        bx, by = self.begin
        ex, ey = self.end
        dbx, dby = bx - px, by - py
        dex, dey = ex - px, ey - py
        if point_type is PT_POSITION:
            self.pos = ox + x, oy + y
            self.begin = ox + x + dbx, oy + y + dby
            self.end = ox + x + dex, oy + y + dey
        elif point_type is PT_CTRL_BEGIN:
            elen: Number = length((dex, dey))
            dbx, dby = (ox + x) - px, (oy + y) - py
            self.begin = ox + x, oy + y
            if self.mode == PM_SMOOTH:
                ex, ey = normal(opposite((dbx, dby)), elen)
                self.end = px + ex, py + ey
            elif self.mode == PM_SYMMETRICAL:
                ex, ey = opposite((dbx, dby))
                self.end = px + ex, py + ey
        elif point_type is PT_CTRL_END:
            self.end = ox + x, oy + y
            blen: Number = length((dbx, dby))
            dex, dey = (ox + x) - px, (oy + y) - py
            self.end = ox + x, oy + y
            if self.mode == PM_SMOOTH:
                bx, by = normal(opposite((dex, dey)), blen)
                self.begin = px + bx, py + by
            elif self.mode == PM_SYMMETRICAL:
                bx, by = opposite((dex, dey))
                self.begin = px + bx, py + by


class Bezier:
    """Bezier class

    Abstracts a modifiable bezier curve that can be used to generate a sequence
    of baked points for use in other places.

    It can be used in quadratic or cubic modes

    :param mode: the `BezierMode`, cubic or quadratic
    :param points: the starting sequence o `Point`s to this bezier"""

    def __init__(self, mode: BezierMode, *points: Point):
        self._points: List[Point] = list(points)
        self._is_cubic: bool = mode is BM_CUBIC

    def __getitem__(self, key) -> Point:
        return self._points.__getitem__(key)

    @property
    def mode(self) -> BezierMode:
        """Gets or sets the mode of this bezier: quadratic or cubic."""
        return BM_CUBIC if self._is_cubic else BM_QUADRATIC
    
    @mode.setter
    def mode(self, value: BezierMode):
        self._is_cubic = value is BM_CUBIC

    def add_point(self, x: Number, y: Number, dist: Number = 10):
        """Adds a bezier `Point`

        :param x: x coordinate of the point
        :param y: y coordinate of the point
        :param dist: axis aligned distance between the point and its control points (default is 10)
        """
        self._points.append(Point(x, y, dist))

    def find_point(self, location: Vec2, margin: int = 2) -> Optional[Tuple[int, PointType, Vec2]]:
        """Returns an index, a point type and an offset if this bezier has a point around `location` and `margin`.

        :param location: the position to test if a bezier point exists
        :param margin: a margin to consider if a point is found
        :returns: a tuple of int, PointType and Vec2 if a point was found, or None otherwise"""
        for i, p in enumerate(self._points):
            res = p.find_point(location, margin)
            if res is not None:
                pty, ofs = res
                if not self._is_cubic and pty is PT_CTRL_END:
                    continue
                return i, pty, ofs
        return None

    def bake_control_points(self) -> Sequence[Vec2]:
        """Returns a sequence of all no positional points of this bezier"""
        points = []
        last = len(self._points) - 1
        if self._is_cubic:
            for i, point in enumerate(self._points):
                if i == 0:
                    points.append(point.begin)
                elif i == last:
                    points.append(point.end)
                else:
                    points.extend((point.end, point.begin))
        else:
            for i, point in enumerate(self._points):
                if i != last:
                    points.append(point.begin)

        return points

    def bake_control_lines(self) -> Sequence[Sequence[Vec2]]:
        """Returns a sequence of lines between control points and its positional points"""
        points = []
        last = len(self._points) - 1
        if self._is_cubic:
            for i, point in enumerate(self._points):
                if i == 0:
                    points.append((point.pos, point.begin))
                elif i == last:
                    points.append((point.pos, point.end))
                else:
                    points.append((point.pos, point.begin))
                    points.append((point.pos, point.end))
        else:
            for i, point in enumerate(self._points):
                if i != last:
                    points.append((point.pos, point.begin))

        return points

    def bake_points(self) -> Sequence[Vec2]:
        """Returns a sequence of control points and positional points"""
        points = []
        last = len(self._points) - 1
        if self._is_cubic:
            for i, point in enumerate(self._points):
                if i == 0:
                    points.extend((point.pos, point.begin))
                elif i == last:
                    points.extend((point.end, point.pos))
                else:
                    points.extend((point.end, point.pos, point.begin))
        else:
            for i, point in enumerate(self._points):
                if i == last:
                    points.append(point.pos)
                else:
                    points.extend((point.pos, point.begin))

        return points

    def bake_pos_points(self) -> Sequence[Vec2]:
        """Returns a sequence of positional points"""
        points = []
        for point in self._points:
            points.append(point.pos)

        return points

    def bake_curve(self, resolution: int = 3) -> Sequence[Vec2]:
        """Generates and returns the curve points from given `resolution` (minimum of 3)

        :param resolution: number of points in each curve segment, higher values produces smoother curves
        :returns: the baked bezier curve
        """
        points = self.bake_points()
        if self._is_cubic:
            return cubic(points, resolution)
        else:
            return quadratic(points, resolution)

# endregion (classes)
# ---------------------------------------------------------
# region FUNCTIONS


# region INTERNAL API


def opposite(p: Vec2) -> Vec2:
    return [-p[0], -p[1]]


def length(p: Vec2) -> Number:
    return math.sqrt(p[0] ** 2 + p[1] ** 2)


def normal(p: Vec2, scale: Number = 1) -> Vec2:
    point_length: int = length(p)
    if point_length != 0:
        return [(p[0] / point_length) * scale, (p[1] / point_length) * scale]
    return [0, 0]


def cubic_segments(x: Union[int, Sequence[Any]]) -> int:
    if not isinstance(x, int):
        try:
            x = len(x)
        except (ValueError, TypeError):
            return 0
    if x < 4:
        return 0
    return int((x - 4) // 3) + 1


def ilerp(a: Number, b: Number, r: float) -> int:
    """Returns the integer linear interpolation between `a` and `b`.

    :param a: the first point
    :param b: the second point
    :param r: the ratio of the interpolation
    :return: returns the interplation based on `r`.
    """
    return int(a + (b - a) * r)


def ilerp2(a: Vec2, b: Vec2, r: float) -> Sequence[int]:
    """Returns the 2d integer vector linear interpolation between `a` and `b`.

        :param a: the first point
        :param b: the second point
        :param r: the ratio of the interpolation
        :return: returns the interplation based on `r`.
        """
    return int(a[0] + (b[0] - a[0]) * r), int(a[1] + (b[1] - a[1]) * r)


def lerp(a: Number, b: Number, r: float) -> float:
    """Returns the float linear interpolation between `a` and `b`.

    :param a: the first point
    :param b: the second point
    :param r: the ratio of the interpolation
    :return: returns the interplation based on `r`.
    """
    return a + (b - a) * r


def lerp2(a: Vec2, b: Vec2, r: float) -> Sequence[float]:
    """Returns the 2d float vector linear interpolation between `a` and `b`.

        :param a: the first point
        :param b: the second point
        :param r: the ratio of the interpolation
        :return: returns the interplation based on `r`.
        """
    return a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r


# endregion (internal api)

# region PUBLIC API


def quadratic(points: Sequence[Vec2], resolution: int) -> Sequence[Vec2]:
    """Returns the baked quadratic bezier curve from the especified sequence of 2d points.

    The sequence length must be always an odd number, being 3 the minimum. `resolution`
    specifies how many points will be generated for each curve segment, also, being 3 the minimum.
    Every second point defines a control point. Control points influentiates only on the curvature
    of the segment between starting points. A segment is a triple of points.

    Raises ValueError if resolution or number o points is below 3 or if number of points is even.

    :param points: the points to generate the bezier curve.
    :param resolution: the number of points in each curve segment.
    :return: a sequence of points forming a curve.
    """

    n = len(points)
    try:
        assert n % 2 == 1, "An odd number of points must be provided."
        assert resolution >= 3, "Resolution is too low."
        assert n >= 3, "Number of points is too low."
    except AssertionError as e:
        raise ValueError(*e.args)

    result: List[Vec2] = []
    steps: int = (n - 1) // 2
    incr: float = 1 / resolution

    r: float
    la: Vec2
    lb: Vec2
    lc: Vec2
    for step in range(steps):
        r = 0.0
        i = step * 2
        for n in range(resolution):
            la = lerp2(points[i], points[i + 1], r)
            lb = lerp2(points[i + 1], points[i + 2], r)
            result.append(lerp2(la, lb, r))
            r += incr
    result.append(points[-1])

    return result


def cubic(points: Sequence[Vec2], resolution: int) -> Sequence[Vec2]:
    """Returns the baked cubic bezier curve from the especified sequence of 2d points.

    The sequence length must be always an odd number, being 4 the minimum. `resolution`
    specifies how many points will be generated for each curve segment, being 3 the minimum.
    Every second and third point defines a control point. Control points influentiates only
    on the curvature (not the location) of the segment between starting points.
    A segment is a quadruple of points. The total number of points must be

    total points = 4 + (n - 1) * 3

    where n is the number of curve segments

    Raises ValueError if resolution or number o points is below 3 or if number of points is even.

    :param points: the points to generate the bezier curve.
    :param resolution: the number of points in each curve segment.
    :return: a sequence of points forming a curve.
    """

    n: int = len(points)
    try:
        assert n >= 4, "Number of points is too low."
        assert (n - 4) % 3 == 0, "Too many or too few points provided."
        assert resolution >= 3, "Resolution is too low."
    except AssertionError as err:
        raise ValueError(*err.args)

    result: List[Vec2] = []
    steps: int = cubic_segments(n)
    incr: float = 1 / resolution

    r: float
    e: Vec2
    f: Vec2
    g: Vec2
    h: Vec2
    i: Vec2
    for step in range(steps):
        r = 0.0
        s = step * 3
        a, b, c, d = points[s: s + 4]
        for n in range(resolution):
            e = lerp2(a, b, r)
            f = lerp2(b, c, r)
            g = lerp2(c, d, r)
            h = lerp2(e, f, r)
            i = lerp2(f, g, r)
            result.append(lerp2(h, i, r))
            r += incr

    result.append(points[-1])

    return result

# endregion (public api)


def main() -> int:
    return 0


# endregion (functions)
# ---------------------------------------------------------
# region ENTRYPOINT


if __name__ == '__main__':
    sys.exit(main())

# endregion (entrypoint)
