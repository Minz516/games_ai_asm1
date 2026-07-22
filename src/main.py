# ============================================================================
# main.py
# Purpose
#   Entry point and game loop. Handles input, updates agents, and draws frames.
# Mental model
#   Each frame: measure dt, process input, update world and agents, draw UI.
#   Agents do not draw themselves until update is finished for the frame.
# Controls
#   Left click sets a target for the frog. Space shoots a bubble. R restarts.
# ============================================================================

import sys, random
import pygame
from settings import *
from utils import draw_grid
from world import World
from entities.frog import Frog
from entities.fly import Fly
from entities.snake import Snake, SnakeState

def draw_vector(surf, origin, vec, color, scale=DEBUG_VECTOR_SCALE, min_len=4.0):
    """Draw a force/velocity vector as a line with a small arrowhead."""
    if vec.length_squared() == 0:
        return
    tip = origin + vec * scale
    if (tip - origin).length() < min_len:
        return
    pygame.draw.line(surf, color, origin, tip, 2)
    direction = (tip - origin).normalize()
    back = direction.rotate(150) * 6
    back2 = direction.rotate(-150) * 6
    pygame.draw.line(surf, color, tip, tip + back, 2)
    pygame.draw.line(surf, color, tip, tip + back2, 2)

def draw_label(surf, font, pos, text, color=DEBUG_TEXT):
    txt = font.render(text, True, color)
    surf.blit(txt, (pos[0] - txt.get_width() // 2, pos[1] - 26))

def draw_debug_frog(surf, frog):
    """Debug overlay for the frog (toggle with 1): arrive target/radii, velocity, braking force."""
    pygame.draw.circle(surf, DEBUG_ARRIVE_SLOW_CIRCLE, frog.target, ARRIVE_SLOW_RADIUS, 1)
    pygame.draw.circle(surf, DEBUG_ARRIVE_STOP_CIRCLE, frog.target, ARRIVE_STOP_RADIUS, 1)
    pygame.draw.circle(surf, DEBUG_CLICK_POINT, frog.target, 4)
    draw_vector(surf, frog.pos, frog.vel, DEBUG_VEL_VECTOR)
    if (frog.target - frog.pos).length() < ARRIVE_SLOW_RADIUS:
        draw_vector(surf, frog.pos, frog.dbg_steer, DEBUG_BRAKE_VECTOR)

def draw_debug_snakes(surf, font, snakes):
    """Debug overlay for snakes (toggle with 2): patrol points, aggro range, state,
    velocity, avoidance rays, and arrive braking/radii."""
    for s in snakes:
        # Patrol path: the waypoints the snake commutes between while patrolling.
        pygame.draw.line(surf, DEBUG_PATROL_LINE, s.home, s.patrol_point, 1)
        pygame.draw.circle(surf, DEBUG_PATROL_LINE, s.home, 5, 1)
        pygame.draw.circle(surf, DEBUG_PATROL_LINE, s.patrol_point, 5, 1)

        # Perception range that drives Patrol -> Aggro in Snake.update().
        pygame.draw.circle(surf, DEBUG_AGGRO_CIRCLE, s.pos, AGGRO_RANGE, 1)

        draw_label(surf, font, s.pos, s.state.name)
        draw_vector(surf, s.pos, s.vel, DEBUG_VEL_VECTOR)

        # Corridors sampled this frame by seek_with_avoid while searching for
        # a free path around obstacles.
        for _angle, end_point, blocked in s.dbg_rays:
            color = DEBUG_RAY_BLOCKED if blocked else DEBUG_RAY_FREE
            pygame.draw.line(surf, color, s.pos, end_point, 1)

        # Arrive slow/stop radii and braking force, only meaningful for the
        # arrive-based states (Patrol*/Harmless), not Aggro (pursue) or
        # Confused (wander).
        if s.dbg_arrive and s.dbg_target is not None:
            pygame.draw.circle(surf, DEBUG_ARRIVE_SLOW_CIRCLE, s.dbg_target, ARRIVE_SLOW_RADIUS, 1)
            pygame.draw.circle(surf, DEBUG_ARRIVE_STOP_CIRCLE, s.dbg_target, ARRIVE_STOP_RADIUS, 1)
            if (s.dbg_target - s.pos).length() < ARRIVE_SLOW_RADIUS:
                draw_vector(surf, s.pos, s.dbg_steer, DEBUG_BRAKE_VECTOR)

def draw_debug_flies(surf, font, flies, frog):
    """Debug overlay for flies (toggle with 3): flee-trigger ranges, state,
    velocity, and boids component vectors."""
    pygame.draw.circle(surf, DEBUG_FLY_SCARE_CIRCLE, frog.pos, FLY_SCARE_BY_FROG_RANGE, 1)
    for b in frog.bubbles:
        pygame.draw.circle(surf, DEBUG_BUBBLE_CIRCLE, b.pos, FLY_BUBBLE_FLEE_RANGE, 1)

    for f in flies:
        draw_label(surf, font, f.pos, f.state.name)
        draw_vector(surf, f.pos, f.vel, DEBUG_VEL_VECTOR)
        draw_vector(surf, f.pos, f.dbg_sep, DEBUG_SEP_VECTOR)
        draw_vector(surf, f.pos, f.dbg_coh, DEBUG_COH_VECTOR)
        draw_vector(surf, f.pos, f.dbg_ali, DEBUG_ALI_VECTOR)

def main():
    # Initialize Pygame and create a window and a clock
    pygame.init()
    pygame.display.set_caption("Frog, Flies, and Snakes")
    # FULLSCREEN switches the display to fullscreen; SCALED keeps the game
    # rendering at the fixed WIDTH x HEIGHT logical resolution (so arena
    # bounds and entity math are untouched) and lets SDL stretch it to fit
    # the actual screen.
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    clock = pygame.time.Clock()

    # Fonts for text and overlay
    font = pygame.font.SysFont("consolas", 22)
    bigfont = pygame.font.SysFont("consolas", 48, bold=True)

    def reset():
        """
        Create a fresh world and agents. Called at start and when the player restarts.
        Returns a tuple of (world, frog, flies, snakes).
        """
        world = World(WIDTH, HEIGHT)
        frog = Frog((WIDTH * 0.5, HEIGHT * 0.5))

        # Randomly scatter flies inside the world bounds
        flies = [Fly((random.randint(60, WIDTH - 60), random.randint(60, HEIGHT - 60)))
                 for _ in range(NUM_FLIES)]

        # Create snakes with patrol points mirrored across the screen
        snakes = []
        for i in range(NUM_SNAKES):
            px = 140 + i * 320
            py = 120 if i % 2 == 0 else HEIGHT - 150
            patrol = (WIDTH - px, HEIGHT - py)
            snakes.append(Snake((px, py), patrol, world.obstacles))

        return world, frog, flies, snakes

    # Build initial state
    world, frog, flies, snakes = reset()

    # Game state for health, scoring, and endings
    health = START_HEALTH
    fly_count = 0
    game_over = False
    win = False

    # Debug overlay toggles, one per agent type so they can be inspected
    # independently instead of all at once: 1 = frog, 2 = snakes, 3 = flies.
    show_debug_frog = False
    show_debug_snakes = False
    show_debug_flies = False

    running = True
    while running:
        # ---------------- Measure dt ----------------
        # Convert milliseconds to seconds for frame rate independent movement
        dt = clock.tick(FPS) / 1000.0

        # ---------------- Input ----------------
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False

                if not game_over and e.key == pygame.K_SPACE:
                    # Space shoots a bubble from the frog mouth
                    frog.shoot()

                if game_over and e.key == pygame.K_r:
                    # R restarts the whole scene
                    world, frog, flies, snakes = reset()
                    health = START_HEALTH
                    fly_count = 0
                    game_over = False
                    win = False

                # Per-agent debug overlays: state, velocity, steering vectors,
                # perception ranges, and obstacle-avoidance rays. See
                # draw_debug_frog()/draw_debug_snakes()/draw_debug_flies() above.
                if e.key == pygame.K_1:
                    show_debug_frog = not show_debug_frog
                    print(f"[debug] frog overlay {'ON' if show_debug_frog else 'OFF'}")
                if e.key == pygame.K_2:
                    show_debug_snakes = not show_debug_snakes
                    print(f"[debug] snake overlay {'ON' if show_debug_snakes else 'OFF'}")
                if e.key == pygame.K_3:
                    show_debug_flies = not show_debug_flies
                    print(f"[debug] fly overlay {'ON' if show_debug_flies else 'OFF'}")

            if not game_over and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # Left click sets a new move target for the frog
                frog.set_target(pygame.mouse.get_pos())

        # ---------------- Update ----------------
        if not game_over:
            # Update frog first since other agents may query frog position
            frog.update(dt)

            # Update flies and check if any fly gets caught by the frog
            for f in list(flies):
                f.update(dt, flies, frog, world.rect, frog.bubbles)

                # Eat a fly when close enough to the frog center
                if (f.pos - frog.pos).length_squared() <= (f.radius + FROG_RADIUS) ** 2:
                    flies.remove(f)
                    fly_count += 1
                    if fly_count >= FLIES_TO_WIN:
                        game_over = True
                        win = True

            # Update snakes and their FSM decisions
            for s in snakes:
                s.update(dt, frog)

            # ------------- Bubble hit logic -------------
            # For each bubble and snake pair, if they overlap:
            #   - pop the bubble
            #   - if the snake is Aggro, switch it to Harmless or Confused
            # This logic is left as a student task to connect FSMs and mechanics.
            for s in snakes:
                for b in frog.bubbles:
                    if (b.pos - s.pos).length_squared() <= (BUBBLE_RADIUS + s.radius) ** 2:
                        if s.state == SnakeState.Aggro: s.set_state(SnakeState.Harmless)
                        # optional: on going harmless to home, then Confused for a short time
                        b.alive = False

            # ------------- Damage logic -------------
            # Only Aggro snakes should damage the frog.
            # Use frog.can_be_hurt() to avoid multiple hits in a row.
            # After a hit, reduce health and optionally pacify the snake.
            for s in snakes:
                if s.state == SnakeState.Aggro and (s.pos - frog.pos).length_squared() <= (s.radius + FROG_RADIUS) ** 2:
                    if frog.can_be_hurt():
                        health -= 1
                        frog.start_hurt()
                        s.set_state(SnakeState.Harmless)
                        if health <= 0:
                            game_over = True
                            win = False

        # ---------------- Draw ----------------
        screen.fill(BG)           # clear background
        draw_grid(screen)         # draw a soft grid
        world.draw(screen)        # draw obstacles

        for f in flies:           # draw flies
            f.draw(screen)
        for s in snakes:          # draw snakes
            s.draw(screen)
        frog.draw(screen)         # draw frog and bubbles

        if show_debug_frog:        # 1: frog arrive target/radii, velocity, braking
            draw_debug_frog(screen, frog)
        if show_debug_snakes:      # 2: snake state, patrol, aggro range, avoidance rays, arrive
            draw_debug_snakes(screen, font, snakes)
        if show_debug_flies:       # 3: fly state, flee ranges, boids vectors
            draw_debug_flies(screen, font, flies, frog)

        # Draw hearts for health
        for i in range(START_HEALTH):
            cx = 16 + i * 35
            cy = 18
            col = RED if i < health else (80, 60, 60)
            pygame.draw.circle(screen, col, (cx, cy), 10)
            pygame.draw.circle(screen, col, (cx + 12, cy), 10)
            points = [(cx - 6, cy + 2), (cx + 18, cy + 2), (cx + 6, cy + 16)]
            pygame.draw.polygon(screen, col, points)

        # Draw fly counter and control hint
        txt = font.render(f"Flies: {fly_count}/{FLIES_TO_WIN}", True, (240, 240, 240))
        screen.blit(txt, (16, 42))
        tips = font.render("Click to move, Space to bubble, R to restart", True, MUTED)
        screen.blit(tips, (16, 68))

        # If game over, dim the screen and show a message
        if game_over:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 160))
            screen.blit(shade, (0, 0))
            msg = "You won!" if win else "You died!"
            col = (90, 220, 120) if win else RED
            text = bigfont.render(msg, True, col)
            hint = font.render("Press R to restart", True, (240, 240, 240))
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10))
            screen.blit(text, rect)
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 44)))

        # Present the frame
        pygame.display.flip()

    # Clean shutdown
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
