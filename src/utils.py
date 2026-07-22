# ============================================================================
# utils.py
# Purpose
#   Small helper functions that do not belong to a specific agent.
#   Drawing helpers and collision checks live here.
# Notes
#   None of these helpers should change game rules or AI decisions.
# ============================================================================

import pygame
from pygame.math import Vector2 as V2
from settings import WIDTH, HEIGHT

# A soft grid color for the background
GRID = (36, 42, 48)

def draw_grid(surf):
    """
    Draw a light grid to help the eye judge motion and distance.
    The grid has no effect on gameplay. It is only visual.
    """
    gap = 36  # distance between grid lines
    # Draw vertical lines
    for x in range(0, WIDTH, gap):
        pygame.draw.line(surf, GRID, (x, 0), (x, HEIGHT))
    # Draw horizontal lines
    for y in range(0, HEIGHT, gap):
        pygame.draw.line(surf, GRID, (0, y), (WIDTH, y))

def clamp(x, a, b):
    """Limit a scalar value x so it stays between a and b inclusive."""
    return max(a, min(b, x))

def limit(v, max_len):
    """
    Limit a vector length.
    If v is longer than max_len, scale it down to exactly max_len.
    """
    if v.length_squared() > max_len * max_len:
        v.scale_to_length(max_len)
    return v

def nearest_point_on_rect(point, rect):
    """Return the closest point on an axis aligned rectangle to a given point."""
    x = clamp(point.x, rect.left, rect.right)
    y = clamp(point.y, rect.top, rect.bottom)
    return V2(x, y)

def circle_rect_intersect(center, radius, rect):
    """Return True if a circle touches or overlaps a rectangle."""
    np = nearest_point_on_rect(center, rect)
    return (center - np).length_squared() <= radius * radius

def push_circle_out_of_rect(pos, radius, rect, skin=1.5):
    """
    If a circle at pos overlaps rect, return the position pushed out to just
    past the rect's edge along the shallowest overlap axis. Otherwise return
    pos unchanged. Pure geometry, used as a hard safety net after
    steering-based avoidance (which only biases velocity gradually and can
    still let a fast, close-range mover overlap an obstacle for a frame).

    `skin` pushes the circle slightly past pure tangency (distance ==
    radius) instead of exactly onto it. Without it, circle_rect_intersect
    treats "touching" as still overlapping, so avoidance logic and this
    correction would keep re-detecting a collision every frame right at the
    boundary and the mover would get stuck pinned against the wall.
    """
    push_distance = radius + skin

    if rect.left <= pos.x <= rect.right and rect.top <= pos.y <= rect.bottom:
        # Center is already inside the rect: push out through whichever
        # edge is closest, since nearest_point_on_rect can't help here
        # (it would just clamp back to pos itself).
        left_pen = pos.x - rect.left
        right_pen = rect.right - pos.x
        top_pen = pos.y - rect.top
        bottom_pen = rect.bottom - pos.y
        min_pen = min(left_pen, right_pen, top_pen, bottom_pen)
        out = V2(pos)
        if min_pen == left_pen:
            out.x = rect.left - push_distance
        elif min_pen == right_pen:
            out.x = rect.right + push_distance
        elif min_pen == top_pen:
            out.y = rect.top - push_distance
        else:
            out.y = rect.bottom + push_distance
        return out

    nearest = nearest_point_on_rect(pos, rect)
    offset = pos - nearest
    dist = offset.length()
    if dist >= radius:
        return pos
    if dist == 0:
        offset = V2(1, 0)
        dist = 0.0001
    return nearest + offset.normalize() * push_distance

def segment_circlecast_hits_rect(p0, p1, radius, rect, step=6.0):
    """
    Approximate a circle cast along a line from p0 to p1.
    We sample points along the segment and test a circle intersect at each step.
    """
    d = p1 - p0
    length = d.length()
    if length == 0:
        return circle_rect_intersect(p0, radius, rect)
    n = max(1, int(length / step))
    for i in range(n + 1):
        t = i / n
        pos = p0 + d * t
        if circle_rect_intersect(pos, radius, rect):
            return True
    return False

def circlecast_hits_any_rect(p0, p1, radius, rects, step=6.0):
    """Return True if the swept circle between p0 and p1 hits any rect in the list."""
    for r in rects:
        if segment_circlecast_hits_rect(p0, p1, radius, r, step):
            return True
    return False
