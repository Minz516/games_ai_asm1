# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

RMIT COSC3145 (Games and AI Techniques) Assignment 1: a 2D predator-prey simulation built with
Python + Pygame. Player controls a frog (click to move, Space to shoot bubbles) that eats flies
while avoiding snakes. This started as an assignment starter with stubbed steering/FSM logic, but
**all required parts are now implemented** — see `PROGRESS.md` for the authoritative, self-audited
checklist of what's done (Parts 1–3 are all checked off; only manual playtesting and submission
steps remain unchecked).

The full assignment brief lives at `../GAIT_Ass1-Description_Sem3 2025.pdf` (one directory above
this folder). It specifies exactly what's graded; check it directly if a task's expected behavior
is ambiguous.

## Running the game

```
cd src
python main.py
```

Requires `pygame` installed (`pip install pygame`). No test suite, linter, or build step exists in
this repo — verification is done by running the game and observing behavior in the window.

Controls: left click sets the frog's move target, Space shoots a bubble, R restarts after game
over, Esc quits, **F1 toggles a debug overlay** (patrol paths + FSM trigger-range rings for aggro/
deaggro/fly panic distances), **H forces all snakes to Harmless** (dev shortcut to observe
Harmless → Confused → PatrolAway without waiting for a real bubble hit or frog bite).

## Architecture

- `src/settings.py` — every tunable constant (speeds, radii, colors, FSM range thresholds, debug
  overlay colors). Change behavior tuning here, not by hardcoding numbers in logic files.
- `src/steering.py` — pure steering-force functions (no entity state). Each function takes
  position/velocity/target and returns a force `Vector2`; callers integrate it via
  `integrate_velocity` (global force cap 550.0, then clamp to the entity's own max speed). Beyond
  the base behaviours (`seek`, `flee`, `arrive`, `boids_separation/cohesion/alignment`,
  `seek_with_avoid`, `pursue`, `evade`, `wander_force`), this file also has two composite helpers
  written to avoid stacking conflicting forces in one state:
  - `arrive_with_avoid` — `arrive`'s slow-down curve but corridor-avoiding at the end instead of
    plain `seek`. Used by every snake Patrol/Harmless state.
  - `pursue_with_avoid` — `pursue`'s velocity-prediction plus corridor avoidance, with a special
    case: if the predicted chase point falls inside an obstacle rect, it redirects to the nearest
    point on that rect's boundary and drops the predicted velocity, so the snake settles at the
    wall instead of jittering into it. Used by snake Aggro.
- `src/utils.py` — geometry/collision helpers (`circle_rect_intersect`, `circlecast_hits_any_rect`,
  `push_circle_out_of_rect`, `nearest_point_on_rect`). `push_circle_out_of_rect` is a hard geometric
  safety net applied every snake frame after steering — steering only biases velocity gradually, so
  a fast close-range chase can still let the snake's circle overlap a rect for a frame; this shoves
  it back out to the rect edge regardless.
- `src/world.py` — builds the static rectangular obstacle set (fixed RNG seed 9, so obstacle layout
  is reproducible across runs) and the arena bounds `Rect`.
- `src/entities/frog.py` — player agent. Uses `arrive` for click-to-move, has a `Bubble` projectile
  class, and a hurt/invulnerability timer (`hurt_timer`, `can_be_hurt()`, `start_hurt()`) wired to
  visual flashing in `draw()` and to the frog-vs-Aggro-snake damage logic in `main.py`.
- `src/entities/fly.py` — `FlyState` FSM (`Flock`, `Fleeing`, `Idle`). `Flock` blends
  `boids_separation/cohesion/alignment` plus a small anchor-to-center force; `Fleeing` uses `evade`
  (predictive flee) against the frog; `Idle` uses `wander_force` with damping. Transitions use
  timers (`scare_timer`, `idle_timer`) to avoid flicker at range boundaries.
- `src/entities/snake.py` — `SnakeState` FSM (`PatrolAway`, `PatrolHome`, `Aggro`, `Harmless`,
  `Confused`), matching the FSM diagram in the PDF (Figure 1). Aggro uses `pursue_with_avoid`;
  Patrol/Harmless states use `arrive_with_avoid`; Confused uses `wander_force` for a timed
  (`confused_timer`) random drift before resuming `PatrolAway`. Also owns a body-trail (`self.trail`)
  for the multi-segment visual body, spaced by distance travelled (not frame count) so segment
  spacing is dt/speed independent, and a tongue-flick animation.
- `src/main.py` — game loop (fixed via `clock.tick(FPS)`, dt in seconds), input handling, world
  reset/restart, F1 debug overlay, and draw order. Snake `update()`, bubble-vs-snake hit resolution
  (pops bubble + pacifies an Aggro snake to Harmless), and frog-vs-Aggro-snake damage logic
  (health -= 1, `frog.start_hurt()`, snake pacified) are all active — not commented out.

## Key data flow

Each frame: read input → update frog → update each fly (needs `flies`, `frog`, world bounds, and
`frog.bubbles` for panic triggers) → update each snake (needs `frog`) → resolve bubble-vs-snake and
frog-vs-snake collisions → draw everything (agents don't draw until all updates for the frame are
done). `dt` (seconds) is threaded through every `update()`/steering call for frame-rate-independent
motion — don't use raw per-frame deltas.

## Working in this repo

- Since every steering function and FSM path is implemented, most future work here is *tuning*
  (`settings.py` constants) or *extending* behavior, not filling in stubs. Before assuming
  something is a TODO, check `PROGRESS.md` and the actual source — the module docstrings in
  `steering.py`/`fly.py`/`snake.py` still read like assignment-stub instructions even though the
  bodies beneath them are filled in.
- The Performance & Tuning and Submission sections of `PROGRESS.md` are intentionally left
  unchecked — they require a human to actually watch the game run or confirm submission logistics,
  not something verifiable by reading code.
