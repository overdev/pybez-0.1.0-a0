# -*- encoding: utf8 -*-
# ------------------------------------------------------------------------------
# pygame_example.py
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

import sys

import pygame as pg
from typing import Optional, List, Sequence, cast

from pybez import Number, Vec2, quadratic, cubic, Bezier, BezierMode, Point, PointMode, PointType

# endregion (imports)
# ---------------------------------------------------------
# region EXPORTS


__all__ = [
    '',
]


# endregion (exports)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS

# endregion (constants)
# ---------------------------------------------------------
# region CLASSES

# endregion (classes)
# ---------------------------------------------------------
# region FUNCTIONS


def render_lines(surface, points, color, backcolor = (192, 192, 192)):
    surface.fill(backcolor)
    pg.draw.aalines(surface, color, False, points)


def hover_point(pt: Sequence[Number], margin: int = 3) -> Optional[Sequence[Number]]:
    x, y = pg.mouse.get_pos()
    px, py = pt
    ox = x - px
    oy = y - py
    if abs(ox) > margin or abs(oy) > margin:
        return None
    return ox, oy


def free() -> int:
    pg.init()

    surface: pg.Surface = pg.display.set_mode((640, 480))

    backcolor = 160, 160, 160
    linecolor = 255, 255, 255
    ctrlline = 192, 192, 192
    ctrlpoint = 192, 128, 32
    dragpoint = 32, 128, 192

    done: bool = False

    is_cubic: bool = True

    cubic_num_points = 7
    cubic_points = [[20 + i * (600 // cubic_num_points), 240] for i in range(cubic_num_points)]

    quadratic_num_points: int = 9
    quadratic_points: Sequence[Sequence[Number]] = [[20 + i * (600 // quadratic_num_points), 240] for i in range(quadratic_num_points)]

    num_points: int = cubic_num_points
    points: Sequence[Sequence[Number]] = cubic_points
    resolution: int = 7

    curve: Sequence[Sequence[Number]] = quadratic(points, resolution)

    render_lines(surface, curve, linecolor, backcolor)

    pg.display.flip()

    dragging: bool = False
    pt_index: int = -1
    offset: Optional[Sequence[Number]] = None
    update: bool = False
    update_curve: bool = False

    while not done:
        ev: pg.event.Event = pg.event.wait()
        if ev.type == pg.QUIT:
            done = True
        elif ev.type == pg.KEYDOWN:
            if ev.key == pg.K_ESCAPE:
                done = True
            elif ev.key == pg.K_q:
                if is_cubic:
                    num_points = quadratic_num_points
                    points = quadratic_points
                    is_cubic = False
                    update_curve = True
                    update = True
            elif ev.key == pg.K_c:
                if not is_cubic:
                    num_points = cubic_num_points
                    points = cubic_points
                    is_cubic = True
                    update_curve = True
                    update = True

        elif ev.type == pg.MOUSEWHEEL:
            resolution = max(3, resolution + ev.y)
            update_curve = True

        elif ev.type == pg.MOUSEMOTION:
            if not dragging:
                pt_index = -1
                for i in range(num_points):
                    offset = hover_point(points[i])
                    if offset is not None:
                        pt_index = i
                        update = True
                        break
            else:
                if pt_index >= 0 and offset is not None:
                    ox, oy = offset
                    mx, my = ev.pos
                    cast(List, points)[pt_index] = [mx + ox, my + oy]
                    update = True
                    update_curve = True

        elif ev.type == pg.MOUSEBUTTONDOWN:
            if pt_index >= 0 and offset is not None:
                dragging = True
                update = True

        elif ev.type == pg.MOUSEBUTTONUP:
            dragging = False
            offset = None
            pt_index = -1
            update = True

        if update_curve:
            if is_cubic:
                curve = cubic(points, resolution)
            else:
                curve = quadratic(points, resolution)

        if update or update_curve:
            render_lines(surface, curve, linecolor, backcolor)

        if update:
            for idx in range(num_points):
                if idx % 2 == 1:
                    pg.draw.aaline(surface, ctrlline, cast(tuple, points[idx - 1]), cast(tuple, points[idx]))
                    pg.draw.aaline(surface, ctrlline, cast(tuple, points[idx]), cast(tuple, points[idx + 1]))

                if pt_index == idx and dragging:
                    px, py = points[pt_index]
                    pg.draw.rect(surface, dragpoint, (px - 3, py - 3, 7, 7))
                else:
                    pg.draw.circle(surface, ctrlpoint, cast(tuple, points[idx]), 3, 1)

        if update or update_curve:
            pg.display.flip()
            update = False
            update_curve = False

    pg.quit()
    return 0


def abstracted() -> int:
    pg.init()

    surface: pg.Surface = pg.display.set_mode((640, 480))

    backcolor = 160, 160, 160
    linecolor = 255, 255, 255
    ctrlline = 192, 192, 192
    ctrlpoint = 192, 128, 32
    lastpoint = 0, 0, 255
    dragpoint = 32, 128, 192

    done: bool = False

    mode: BezierMode = BezierMode.CUBIC
    bezier_size: int = 4
    bezier: Bezier = Bezier(mode, *(Point(20 + i * (600 // bezier_size), 240) for i in range(bezier_size)))

    resolution: int = 7

    curve: Sequence[Vec2] = bezier.bake_curve(resolution)

    render_lines(surface, curve, linecolor, backcolor)

    pg.display.flip()

    dragging: bool = False
    pt_index: int = -1
    pt_last: int = -1
    pt_type: PointType = PointType.POSITION
    offset: Optional[Vec2] = None
    update: bool = False
    update_curve: bool = False

    while not done:
        ev: pg.event.Event = pg.event.wait()
        if ev.type == pg.QUIT:
            done = True
        elif ev.type == pg.KEYDOWN:
            if ev.key == pg.K_ESCAPE:
                done = True
            elif ev.key == pg.K_q:
                if bezier.mode is BezierMode.CUBIC:
                    bezier.mode = BezierMode.QUADRATIC
                    update_curve = True
                    update = True
            elif ev.key == pg.K_c:
                if bezier.mode is BezierMode.QUADRATIC:
                    bezier.mode = BezierMode.CUBIC
                    update_curve = True
                    update = True
            elif ev.key == pg.K_1:
                if pt_last >= 0:
                    bezier[pt_last].mode = PointMode.CUSP
            elif ev.key == pg.K_2:
                if pt_last >= 0:
                    bezier[pt_last].mode = PointMode.SMOOTH
            elif ev.key == pg.K_3:
                if pt_last >= 0:
                    bezier[pt_last].mode = PointMode.SYMMETRICAL

        elif ev.type == pg.MOUSEWHEEL:
            resolution = max(3, resolution + ev.y)
            update_curve = True

        elif ev.type == pg.MOUSEMOTION:
            if not dragging:
                pt_index = -1
                offset = None
                res = bezier.find_point(ev.pos, 3)
                if res:
                    pt_index, pt_type, offset = res
            else:
                if pt_index >= 0 and offset is not None:
                    ox, oy = offset
                    mx, my = ev.pos
                    pt = [mx + ox, my + oy]
                    bezier[pt_index].move_point(pt_type, pt, offset)
                    update = True
                    update_curve = True

        elif ev.type == pg.MOUSEBUTTONDOWN:
            if pt_index >= 0 and offset is not None:
                dragging = True
                update = True
                pt_last = pt_index

        elif ev.type == pg.MOUSEBUTTONUP:
            dragging = False
            offset = None
            pt_index = -1
            update = True

        if update_curve:
            curve = bezier.bake_curve(resolution)

        if update or update_curve:
            render_lines(surface, curve, linecolor, backcolor)

        if update:
            for (px, py) in bezier.bake_control_points():
                pg.draw.rect(surface, dragpoint, (px - 3, py - 3, 7, 7))
            for i, (px, py) in enumerate(bezier.bake_pos_points()):
                if i == pt_last:
                    pg.draw.rect(surface, lastpoint, (px - 4, py - 4, 9, 9), 1)
                pg.draw.rect(surface, ctrlpoint, (px - 3, py - 3, 7, 7))
            for (a, b) in bezier.bake_control_lines():
                pg.draw.aaline(surface, ctrlline, a, b)

        if update or update_curve:
            pg.display.flip()
            update = False
            update_curve = False

    pg.quit()
    return 0


def main() -> int:
    return abstracted()


# endregion (functions)
# ---------------------------------------------------------
# region ENTRYPOINT


if __name__ == '__main__':
    sys.exit(main())

# endregion (entrypoint)
