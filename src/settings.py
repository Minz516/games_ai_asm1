# ============================================================================
# settings.py
# Purpose
#   Central place for all constants and tuning values.
#   You can tweak speeds, radii, and counts here without touching logic.
# Reading guide
#   Each variable has a short note so you know what it controls.
# ============================================================================

# Window size in pixels
WIDTH, HEIGHT = 1000, 700

# Target frames per second for the game loop
FPS = 60

# Colors as RGB tuples. Used by drawing code for the UI and agents.
BG    = (28, 33, 38)     # background color
WHITE = (240, 240, 240)  # text and highlights
GREEN = (90, 220, 120)   # frog color
BLUE  = (120, 180, 250)  # bubble color
YELLOW= (250, 225, 120)  # fly color when flocking or idle
PURPLE= (185, 120, 250)  # fly color when fleeing
RED   = (232, 88, 88)    # health hearts
MUTED = (180, 188, 196)  # hint text

# Frog setup
FROG_RADIUS = 16          # draw size and collision size for the frog
FROG_SPEED  = 150.0       # top speed for the frog in pixels per second
HURT_INVULN = 1.0         # seconds of temporary invulnerability after damage

# Bubble setup
BUBBLE_RADIUS   = 8       # visual radius and collision radius
BUBBLE_SPEED    = 380.0   # how fast the bubble travels
BUBBLE_LIFETIME = 2.0     # seconds before the bubble pops automatically

# Fly setup
NUM_FLIES = 18            # how many flies spawn
FLY_RADIUS = 8            # fly draw and collision radius
FLY_SPEED  = 110.0        # fly max speed

# Boids neighborhood and weights
# These determine how flies react to neighbors
NEIGHBOR_RADIUS = 120.0   # how far a fly considers other flies as neighbors
SEP_RADIUS      = 50.0    # separation threshold distance
SEP_WEIGHT      = 1.9     # weight for separation force
COH_WEIGHT      = 0.9     # weight for cohesion force
ALI_WEIGHT      = 0.8     # weight for alignment force
ANCHOR_WEIGHT   = 0.6     # small pull to arena center to keep flock on screen

# Fly perception ranges for FSM transitions
FLY_SCARE_BY_FROG_RANGE = 160.0   # panic if the frog comes within this range
FLY_BUBBLE_FLEE_RANGE   = 140.0   # panic if a bubble comes within this range
FLY_STOP_FLEEING_RANGE  = 220.0   # calm down once both frog and bubbles are beyond this
FLY_IDLE_DISTANCE       = 300.0   # far enough from the frog to consider idling
FLY_IDLE_DELAY          = 2.0     # seconds of calm/far time before entering Idle

# Arrive behavior
# Slow inside slow radius and stop inside stop radius
ARRIVE_SLOW_RADIUS = 100.0
ARRIVE_STOP_RADIUS = 20.0
ARRIVE_BRAKE_GAIN = 5.0

# Snake setup
NUM_SNAKES  = 0
SNAKE_RADIUS = 18
SNAKE_SPEED  = 80.0

# Snake perception ranges for FSM transitions
AGGRO_RANGE   = 150.0     # start chasing when frog gets this close
DEAGGRO_RANGE = 150.0     # stop chasing when frog moves this far

# Obstacle avoidance tuning
AVOID_LOOKAHEAD       = 110.0   # how far the snake looks ahead when checking a corridor
AVOID_ANGLE_INCREMENT = 12      # degrees to rotate per step when searching for a free path
AVOID_MAX_ANGLE       = 90      # maximum deviation to try on either side

# Game rules
START_HEALTH = 10                 # how many hits the frog can take
FLIES_TO_WIN = 10                # win condition counter

# Debug overlay (toggled with F1 in main.py)
DEBUG_VECTOR_SCALE     = 0.5             # pixels-per-unit-force scale when drawing vectors as lines
DEBUG_TEXT             = (235, 235, 235) # state labels

# Snake overlay
DEBUG_PATROL_LINE      = (140, 140, 190) # line + waypoint markers for snake patrol path
DEBUG_AGGRO_CIRCLE     = (255, 120, 120) # ring at AGGRO_RANGE around each snake: Aggro trigger
DEBUG_ARRIVE_SLOW_CIRCLE = (120, 200, 255) # ring at ARRIVE_SLOW_RADIUS around the snake's target
DEBUG_ARRIVE_STOP_CIRCLE = (255, 120, 160) # ring at ARRIVE_STOP_RADIUS around the snake's target
DEBUG_RAY_FREE         = (120, 255, 150) # obstacle-avoidance corridor sample: not blocked
DEBUG_RAY_BLOCKED      = (255, 90, 90)   # obstacle-avoidance corridor sample: blocked

# Fly overlay
DEBUG_FLY_SCARE_CIRCLE = (200, 120, 250) # ring at FLY_SCARE_BY_FROG_RANGE around the frog: Flee trigger
DEBUG_BUBBLE_CIRCLE    = (120, 180, 255) # ring at FLY_BUBBLE_FLEE_RANGE around each bubble: Flee trigger
DEBUG_FLY_IDLE_CIRCLE  = (255, 210, 100) # ring at FLY_IDLE_DISTANCE around the frog: Flock <-> Idle trigger
DEBUG_WANDER_CIRCLE    = (150, 150, 255) # wander circle projected in front of an Idle fly
DEBUG_WANDER_POINT     = (255, 255, 255) # the point chosen on the wander circle this frame
DEBUG_SEP_VECTOR       = (255, 120, 120) # boids separation component
DEBUG_COH_VECTOR       = (120, 220, 255) # boids cohesion component
DEBUG_ALI_VECTOR       = (150, 255, 150) # boids alignment component

# Frog overlay
DEBUG_CLICK_POINT      = (255, 255, 255) # last click target
DEBUG_VEL_VECTOR       = (255, 255, 255) # current velocity, drawn for all three agent types
DEBUG_DESIRED_VECTOR   = (255, 255, 0)   # desired velocity (target heading before steering is applied)
DEBUG_STEER_VECTOR     = (255, 0, 255)   # steering force actually applied this frame (frog + snake)
