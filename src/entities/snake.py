# ============================================================================
# snake.py
# Purpose
#   Predator agent with a five-state FSM.
#   States: PatrolAway, PatrolHome, Aggro, Harmless, Confused.
#   Aggro chases the frog. Harmless returns home after pacification.
#   Confused wanders briefly after reaching home, then resumes patrol.
# Update order
#   Evaluate transitions first, then run the behavior for the active state.
# Drawing
#   Plain circle only, colored by state.
# ============================================================================

from enum import Enum, auto
import random
import pygame
from pygame.math import Vector2 as V2
from settings import (
    WIDTH, HEIGHT, WHITE,
    SNAKE_RADIUS, SNAKE_SPEED, AGGRO_RANGE, DEAGGRO_RANGE,
    ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS
)
from steering import integrate_velocity, wander_force, arrive_with_avoid, pursue_with_avoid
from utils import push_circle_out_of_rect

class SnakeState(Enum):
    PatrolAway = auto()
    PatrolHome = auto()
    Aggro      = auto()
    Harmless   = auto()
    Confused   = auto()

class Snake:
    def __init__(self, pos, patrol_point, rects):
        # Motion and shape
        self.pos = V2(pos)
        self.vel = V2(1, 0)
        self.radius = SNAKE_RADIUS
        self.speed = SNAKE_SPEED

        # Home base and patrol destination
        self.home = V2(pos)
        self.patrol_point = V2(patrol_point)

        # Initial state
        self.state = SnakeState.PatrolAway

        # Obstacles for avoidance
        self.rects = rects

        # Color varies by state for quick visual debug
        self.color = (190, 130, 110)

        # Facing direction for the eyes, kept from the last non-zero velocity
        # so the eyes don't snap to a default when the snake is briefly still.
        self.facing = V2(1, 0)

        # Confused state timer
        self.confused_timer = 0.0

        # Confused angle
        self.wander_angle = 0.0

        # RNG for wander if needed
        self._rng_seed = random.randint(0, 999999)

        self._rng = random.Random(self._rng_seed)

        # Debug-only, for the F1 overlay:
        self.dbg_target = None       # current arrive/pursue target point, if any
        self.dbg_rays = []           # (angle_deg, end_point, blocked) tested this frame
        self.dbg_steer = V2()        # last steering force
        self.dbg_desired = V2()      # desired velocity the steering force is steering toward
        self.dbg_arrive = False      # whether the current state uses arrive (slow/stop radii apply)

    def set_state(self, st):
        """Switch to a new FSM state."""
        self.state = st

    def update(self, dt, frog):
        """
        Update state transitions based on distance to frog and timers.
        Then compute a steering force for the active state and integrate motion.
        """

        # Distance to frog for transitions
        dist = (frog.pos - self.pos).length()

        # ---------------- FSM transitions ----------------
        if self.state == SnakeState.Aggro:
            if dist > DEAGGRO_RANGE:
                self.set_state(SnakeState.PatrolHome)

        elif self.state in (SnakeState.PatrolHome, SnakeState.PatrolAway):
            if dist < AGGRO_RANGE:
                self.set_state(SnakeState.Aggro)

        elif self.state == SnakeState.Harmless:
            # When harmless snake reaches home, enter Confused briefly then resume patrol
            if (self.home - self.pos).length() < 12:
                self.confused_timer = 1.5  # seconds of confusion
                self.set_state(SnakeState.Confused)

        elif self.state == SnakeState.Confused:
            self.confused_timer -= dt
            if self.confused_timer <= 0:
                self.set_state(SnakeState.PatrolAway)

        # ---------------- State behaviours ----------------
        self.dbg_rays = []
        self.dbg_arrive = False

        if self.state == SnakeState.Aggro:
            self.color = (255, 150, 150)
            self.dbg_target = V2(frog.pos)
            steer = pursue_with_avoid(self.pos, self.vel, frog.pos, frog.vel, self.speed,
                                       self.radius, self.rects, debug_rays=self.dbg_rays)

        elif self.state == SnakeState.PatrolAway:
            self.color = (180, 200, 255)
            self.dbg_target = V2(self.patrol_point)
            self.dbg_arrive = True
            steer = arrive_with_avoid(self.pos, self.vel, self.patrol_point, self.speed,
                                       self.radius, self.rects, debug_rays=self.dbg_rays)
            if (self.patrol_point - self.pos).length() < 25:
                self.set_state(SnakeState.PatrolHome)

        elif self.state == SnakeState.PatrolHome:
            self.color = (180, 220, 180)
            self.dbg_target = V2(self.home)
            self.dbg_arrive = True
            steer = arrive_with_avoid(self.pos, self.vel, self.home, self.speed,
                                       self.radius, self.rects, debug_rays=self.dbg_rays)
            if (self.home - self.pos).length() < 25:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            self.color = (190, 180, 255)
            self.dbg_target = V2(self.home)
            self.dbg_arrive = True
            steer = arrive_with_avoid(self.pos, self.vel, self.home, self.speed * 0.9,
                                       self.radius, self.rects, debug_rays=self.dbg_rays)

        else:  # Confused
            self.color = (245, 210, 160)
            self.dbg_target = None
            steer, self.wander_angle = wander_force(self.vel, self.wander_angle, rng_seed=self._rng)

        self.dbg_steer = steer
        # desired velocity = velocity before this frame's steering is applied,
        # plus the steering force (steer == desired - vel for seek/arrive/pursue).
        self.dbg_desired = self.vel + steer

        # Integrate velocity and update position
        self.vel = integrate_velocity(self.vel, steer, dt, self.speed)
        self.pos += self.vel * dt

        if self.vel.length_squared() > 16:
            self.facing = self.vel.normalize()

        # Keep inside arena
        if self.pos.x < self.radius: self.pos.x = self.radius
        if self.pos.x > WIDTH - self.radius: self.pos.x = WIDTH - self.radius
        if self.pos.y < self.radius: self.pos.y = self.radius
        if self.pos.y > HEIGHT - self.radius: self.pos.y = HEIGHT - self.radius

        # Hard safety net: steering-based avoidance only biases velocity
        # gradually (see integrate_velocity's force cap), so a close, fast
        # pursuit can still let the snake's circle overlap a rect for a
        # frame before the steering fully turns it away. Push the snake back
        # out to the rect's edge so it never visually sits inside an
        # obstacle, no matter how the chase played out this frame.
        for rect in self.rects:
            self.pos = push_circle_out_of_rect(self.pos, self.radius, rect)

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, self.pos, self.radius)

        # Two eyes on either side of the facing direction
        side = self.facing.rotate(90)
        for sign in (1, -1):
            eye_pos = self.pos + self.facing * (self.radius * 0.45) + side * (self.radius * 0.5 * sign)
            pygame.draw.circle(surf, (30, 30, 30), eye_pos, 3)
            pygame.draw.circle(surf, WHITE, eye_pos, 5, 1)
