# ============================================================================
# steering.py
# Purpose
#   Implement all steering behaviours here. Each function computes a steering
#   force vector. Entities apply that force to their velocity each frame.
# Key idea
#   desired_velocity minus current_velocity gives the steering force.
#   Use dt in update loops when integrating velocity to keep motion consistent.
# ============================================================================

import math
from pygame.math import Vector2 as V2
from utils import limit, circlecast_hits_any_rect, nearest_point_on_rect
from settings import (
    ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS,
    AVOID_LOOKAHEAD, AVOID_ANGLE_INCREMENT, AVOID_MAX_ANGLE, ARRIVE_BRAKE_GAIN
)
import random

# ---------------- Base behaviours ----------------

def seek(pos, vel, target, max_speed):
    """
    Move toward a target. Returns a steering force.
    desired = direction_to_target * max_speed
    steering = desired - current_velocity
    """
    seek_vector = target - pos
    if seek_vector.length_squared() == 0:
        return V2()
    desired_velocity = seek_vector.normalize() * max_speed
    return desired_velocity - vel

def flee(pos, vel, target, max_speed):
    """
    Move away from a target. This is the opposite of seek.
    You need to implement the mirror of seek using direction from threat to self.
    """
    # Find the direction that go away from the threat (target)
    threat_vector = pos - target
    # If the threat_vector is zero, return a zero vector to avoid division by zero
    if threat_vector.length_squared() == 0:
        return V2()
    # Normalize the threat_vector and scale it to max_speed to get the desired velocity
    desired_velocity = threat_vector.normalize() * max_speed
    # Return the steering force, which is the difference between desired velocity and current velocity
    return desired_velocity - vel

def arrive(pos, vel, target, max_speed, slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS, break_gain=ARRIVE_BRAKE_GAIN):
    """
    Like seek when far, but slow down near the target.
    Rules
      If distance < stop_radius, return a force that cancels leftover velocity
      If distance < slow_radius, scale desired speed by distance / slow_radius
      Otherwise use full speed
    This should remove overshoot and jitter around the target.
    """
    # Compute the vector from the current position to the target
    seek_vector = target - pos
    # Calculate the distance to the target
    distance = seek_vector.length()
    # If the distance is zero, return a zero vector to avoid division by zero
    if distance == 0:
        return V2()
    
    # Determine the desired speed based on the distance to the target
    if distance < slow_radius:
        # If the distance is less than the stop radius, return a force that cancels leftover velocity
        if distance < stop_radius:
            braking_force = seek(pos, vel, target, 0.0) * break_gain
            return braking_force
        else:
            desired_speed = max_speed * (distance / slow_radius)
    else:
        desired_speed = max_speed

    return seek(pos, vel, target, desired_speed)

def integrate_velocity(vel, force, dt, max_speed):
    """
    Apply a steering force to velocity using Euler integration.
    Then clamp to max speed and return the new velocity.
    Use this inside agent update methods after computing steering forces.
    """
    vel += limit(force, 500.0) * dt
    if vel.length() > max_speed:
        vel.scale_to_length(max_speed)
    return vel

# ---------------- Boids components ----------------

def boids_separation(me_pos, neighbors, sep_radius):
    """
    Push away from neighbors that are too close.
    neighbors: list of tuples (neighbor_pos, neighbor_vel)
    Typical approach
      For each neighbor inside sep_radius, add a vector pointing away with
      magnitude inversely proportional to distance. Normalize at the end.
    """
    push_away = V2()
    for n in neighbors:
        direction_vector = me_pos - n[0]
        distance = direction_vector.length()
        if distance < sep_radius and distance > 0:
            strength = sep_radius - distance # stronger when closer
            push_away += direction_vector.normalize() * strength

    return push_away

def boids_cohesion(me_pos, neighbors):
    """
    Pull toward the average position of neighbors.
    Typical approach
      Compute the center of mass of neighbors then steer toward that point.
    """
    if len(neighbors) == 0:
        return V2()
    
    center_position = V2()

    for n in neighbors:
        center_position += n[0]    

    return center_position / len(neighbors) - me_pos

def boids_alignment(me_vel, neighbors):
    """
    Match the average velocity of neighbors.
    Typical approach
      Compute the average heading of neighbors then steer toward that heading.
    """
    if len(neighbors) == 0:
        return V2()
    
    average_velocity = V2()

    for n in neighbors:
        average_velocity += n[1]

    return average_velocity / len(neighbors) - me_vel

# ---------------- Obstacle avoidance blend ----------------

def seek_with_avoid(pos, vel, target, max_speed, radius, rects, lookahead=AVOID_LOOKAHEAD, debug_rays=None):
    """
    Seek the target but avoid obstacles by sampling angled corridors.
    Idea
      1. Check a straight corridor first
      2. If blocked, rotate small angles left and right until a free path is found
      3. Use that direction for the seek
      4. If all blocked, apply a small braking force
    Use circlecast_hits_any_rect to test each corridor.

    debug_rays, if given a list, gets one (angle_deg, end_point, blocked) tuple
    appended per corridor actually tested this call, purely for visualization.
    """
    seek_direction = target - pos
    if seek_direction.length_squared() == 0:
        return V2()

    unit_direction = seek_direction.normalize()
    test_distance = min(lookahead, seek_direction.length())
    test_point = pos + unit_direction * test_distance
    blocked = circlecast_hits_any_rect(pos, test_point, radius, rects)
    if debug_rays is not None:
        debug_rays.append((0.0, test_point, blocked))
    if not blocked:
        return seek(pos, vel, target, max_speed)

    angle = AVOID_ANGLE_INCREMENT
    while angle <= AVOID_MAX_ANGLE:
        left_direction = unit_direction.rotate(angle)
        right_direction = unit_direction.rotate(-angle)
        left_point = pos + left_direction * test_distance
        right_point = pos + right_direction * test_distance

        left_blocked = circlecast_hits_any_rect(pos, left_point, radius, rects)
        if debug_rays is not None:
            debug_rays.append((angle, left_point, left_blocked))
        if not left_blocked:
            return seek(pos, vel, left_point, max_speed)

        right_blocked = circlecast_hits_any_rect(pos, right_point, radius, rects)
        if debug_rays is not None:
            debug_rays.append((-angle, right_point, right_blocked))
        if not right_blocked:
            return seek(pos, vel, right_point, max_speed)

        angle += AVOID_ANGLE_INCREMENT

    slide_direction = unit_direction.rotate(90)
    return slide_direction * max_speed - vel

def arrive_with_avoid(pos, vel, target, max_speed, radius, rects, slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS, lookahead=AVOID_LOOKAHEAD, debug_rays=None, break_gain=ARRIVE_BRAKE_GAIN):
    """
    Like arrive(), but uses seek_with_avoid() instead of seek() at the end,
    so the snake both slows near the target AND avoids obstacles along the way.
    """
    seek_vector = target - pos
    distance = seek_vector.length()
    if distance == 0:
        return V2()

    if distance < slow_radius:
        if distance < stop_radius:
            braking_force = seek(pos, vel, target, 0.0) * break_gain
            return braking_force
        else:
            desired_speed = max_speed * (distance / slow_radius)
    else:
        desired_speed = max_speed

    return seek_with_avoid(pos, vel, target, desired_speed, radius, rects, lookahead, debug_rays=debug_rays)

def pursue_with_avoid(pos, vel, target_pos, target_vel, max_speed, radius, rects, lookahead=AVOID_LOOKAHEAD, debug_rays=None):
    """
    Like pursue(), but uses seek_with_avoid() instead of seek() at the end,
    so the snake both predicts the target AND avoids obstacles along the way.

    If target_pos itself is inside an obstacle rect, seeking straight at it is
    unsolvable for seek_with_avoid: every swept corridor near the wall stays
    blocked, so the pursuer just keeps pressing into the wall every frame
    instead of settling. Redirect the chase point to the nearest spot on that
    rect's boundary instead, and drop the predicted velocity (a target tucked
    inside cover isn't meaningfully "moving" for interception purposes) so
    the pursuer comes to rest at the wall rather than jittering against it.
    """
    chase_target = target_pos
    chase_vel = target_vel
    for rect in rects:
        if rect.collidepoint(chase_target.x, chase_target.y):
            chase_target = nearest_point_on_rect(chase_target, rect)
            chase_vel = V2()
            break

    direction_to_target = chase_target - pos
    distance = direction_to_target.length()
    if distance == 0:
        return V2()

    time_horizon = distance / (max_speed + 0.001)  # small epsilon to avoid division by zero
    predicted_position = chase_target + chase_vel * time_horizon
    return seek_with_avoid(pos, vel, predicted_position, max_speed, radius, rects, lookahead, debug_rays=debug_rays)

# ---------------- New behaviours to be implemented ----------------

def pursue(pos, vel, target_pos, target_vel, max_speed):
    """
    Predict the future position of the target then seek that point.
    Suggested
      distance = |target_pos - pos|
      time_horizon = distance / (max_speed + small_eps)
      predicted    = target_pos + target_vel * time_horizon
      return seek toward predicted
    Replace simple seek in Snake Aggro with pursue for better interception.
    """
    direction_to_target = target_pos - pos
    distance = direction_to_target.length()
    if distance == 0:
        return V2()
    
    time_horizon = distance / (max_speed + 0.001)  # small epsilon to avoid division by zero
    predicted_position = target_pos + target_vel * time_horizon
    return seek(pos, vel, predicted_position, max_speed)

def evade(pos, vel, threat_pos, threat_vel, max_speed):
    """
    Predict the future position of a threat then flee from that point.
    This is the inverse of pursue. Use the same prediction idea.
    """
    direction_away_from_threat = pos - threat_pos
    distance = direction_away_from_threat.length()
    if distance == 0:
        return V2()
    time_horizon = distance / (max_speed + 0.001)  # small epsilon to avoid division by zero
    predicted_threat_position = threat_pos + threat_vel * time_horizon
    return flee(pos, vel, predicted_threat_position, max_speed)

def wander_force(me_vel, wander_angle, jitter_deg=12.0, circle_distance=24.0, circle_radius=18.0, rng_seed=None):
    """
    Return a small random steering vector for gentle drift.
    Classic wander
      Project a small circle ahead along current heading, then jitter the
      target point on that circle by a tiny random angle each update.
    Use this for Fly Idle and Snake Confused.
    """
    if me_vel.length_squared() == 0:
        return V2(1, 0), wander_angle
    
    # Compute the forward direction and the center of the wander circle
    forward_direction = me_vel.normalize()
    circle_center = forward_direction * circle_distance

    # Jitter the wander angle by a small random amount
    wander_angle += rng_seed.uniform(-jitter_deg, jitter_deg)

    # Compute the target point on the circle using the updated wander angle
    target_point_on_circle = V2(math.cos(math.radians(wander_angle)), math.sin(math.radians(wander_angle))) * circle_radius

    # Compute the final wander target by adding the circle center and the target point on the circle
    wander_target = circle_center + target_point_on_circle
    return wander_target, wander_angle


