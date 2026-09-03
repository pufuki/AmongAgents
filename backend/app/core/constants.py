"""Game constants for Among Agents."""

# Game configuration
NUM_AGENTS = 5
NUM_MAFIA = 1
NUM_DETECTIVE = 1
NUM_CITIZENS = 3

# Roles
ROLE_MAFIA = "mafia"
ROLE_DETECTIVE = "detective"
ROLE_CITIZEN = "citizen"

# Phases
PHASE_NIGHT = "night"
PHASE_DAY_DISCUSSION = "day_discussion"
PHASE_DAY_VOTING = "day_voting"
PHASE_DAY_RESULT = "day_result"
PHASE_GAME_OVER = "game_over"

# Game states
STATE_WAITING = "waiting"
STATE_ACTIVE = "active"
STATE_FINISHED = "finished"

# Autoplay delay in milliseconds
AUTOPLAY_DELAY_MS = 1500

# Agent names
AGENT_NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve"]

# Personalities
PERSONALITIES = ["analytical", "aggressive", "diplomatic", "quiet", "chaotic"]
