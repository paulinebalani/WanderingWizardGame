import pygame
import random
import math

from characters import Wizard, GrimReaper
from settings import Settings

# ─────────────────────────────────────────────────────────────
# Lightning & casting visual constants
# ─────────────────────────────────────────────────────────────
LIGHTNING_SEGMENTS  = 12    # number of jagged segments per bolt
LIGHTNING_DEVIATION = 22    # max pixel deviation per segment (jaggedness)
LIGHTNING_BRANCHES  = 3     # number of smaller side branches
LIGHTNING_COLORS    = [     # core → outer glow layers
    (255, 255, 255),        # white core
    (180, 180, 255),        # pale violet inner
    (80,  80,  255),        # blue mid
    (30,  10,  160),        # deep blue outer glow
]
LIGHTNING_WIDTHS    = [2, 3, 5, 8]   # stroke width per layer (outermost first)
CAST_GLOW_COLORS    = [
    (255, 255, 120, 180),   # yellow-white inner glow  (RGBA)
    (100, 100, 255, 100),   # blue mid glow
    (50,   50, 200,  40),   # deep blue outer glow
]
CAST_GLOW_RADII     = [18, 34, 52]   # radius of each glow ring


# ─────────────────────────────────────────────────────────────
# Lightning drawing helpers
# ─────────────────────────────────────────────────────────────
def _jagged_points(start, end, segments, deviation):
    """Return a list of points forming a jagged line from start to end."""
    points = [start]
    for i in range(1, segments):
        t      = i / segments
        mx     = start[0] + (end[0] - start[0]) * t
        my     = start[1] + (end[1] - start[1]) * t
        dx     = end[0] - start[0]
        dy     = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy) or 1
        perp_x = -dy / length
        perp_y =  dx / length
        offset = random.uniform(-deviation, deviation)
        points.append((mx + perp_x * offset, my + perp_y * offset))
    points.append(end)
    return points


def draw_lightning_bolt(surface, start, end,
                        segments=LIGHTNING_SEGMENTS,
                        deviation=LIGHTNING_DEVIATION,
                        branches=LIGHTNING_BRANCHES,
                        alpha=255):
    """
    Draw a multi-layer glowing jagged lightning bolt from start to end.
    Uses a temporary SRCALPHA surface so we can respect the alpha arg.
    """
    sx, sy = int(start[0]), int(start[1])
    ex, ey = int(end[0]),   int(end[1])

    pad = LIGHTNING_WIDTHS[-1] + deviation + 10
    lx  = min(sx, ex) - pad
    ty  = min(sy, ey) - pad
    w   = abs(ex - sx) + pad * 2
    h   = abs(ey - sy) + pad * 2

    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    tmp.set_alpha(alpha)

    os_ = (sx - lx, sy - ty)
    oe_ = (ex - lx, ey - ty)

    seed = random.randint(0, 10000)
    random.seed(seed)
    pts     = _jagged_points(os_, oe_, segments, deviation)
    int_pts = [(int(x), int(y)) for x, y in pts]

    for color, width in zip(reversed(LIGHTNING_COLORS), reversed(LIGHTNING_WIDTHS)):
        if len(int_pts) >= 2:
            pygame.draw.lines(tmp, color, False, int_pts, width)

    for _ in range(branches):
        bi     = random.randint(1, len(pts) - 2)
        bx, by = pts[bi]
        angle  = random.uniform(0, math.pi * 2)
        blen   = random.uniform(20, 60)
        bend   = (bx + math.cos(angle) * blen, by + math.sin(angle) * blen)
        bpts   = _jagged_points((bx, by), bend, 5, deviation // 2)
        ibpts  = [(int(x), int(y)) for x, y in bpts]
        if len(ibpts) >= 2:
            pygame.draw.lines(tmp, LIGHTNING_COLORS[1], False, ibpts, 1)

    random.seed()
    surface.blit(tmp, (lx, ty))


def draw_cast_glow(surface, center):
    """
    Draw the wizard's casting glow: layered translucent circles at the
    wizard's staff-tip position.
    """
    for radius, rgba in zip(CAST_GLOW_RADII, CAST_GLOW_COLORS):
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, rgba, (radius, radius), radius)
        surface.blit(glow, (center[0] - radius, center[1] - radius))

    spark = pygame.Surface((12, 12), pygame.SRCALPHA)
    pygame.draw.circle(spark, (255, 255, 255, 220), (6, 6), 6)
    surface.blit(spark, (center[0] - 6, center[1] - 6))


# ─────────────────────────────────────────────────────────────
# Casting helpers — extend Wizard at runtime
# These functions operate on a Wizard instance but live here so
# that characters.py stays free of any power / rendering logic.
# ─────────────────────────────────────────────────────────────
def wizard_cast_origin(wizard):
    """
    Return the world-space staff-tip position for a Wizard instance.
    The staff is held on the leading side of the sprite, so the x offset
    shifts right when facing right and left when facing left.
    """
    base_x, base_y = wizard.cast_hand_offset   # (110, 20) — centre of sprite

    # Push the origin to the edge of the sprite on whichever side the staff is
    if wizard.facing == 'left':
        x = wizard.rect.left + (base_x - 60)   # shift toward left edge
    else:                                        # 'right' or 'front'
        x = wizard.rect.left + (base_x + 60)   # shift toward right edge

    y = wizard.rect.top + base_y
    return (x, y)


def wizard_blit_cast_effect(wizard):
    """
    Draw the casting glow around the wizard's staff tip.
    Call AFTER blit_wizard() so it renders on top.
    Only draws when wizard.is_casting is True.
    """
    if not wizard.is_casting:
        return
    center = wizard_cast_origin(wizard)
    draw_cast_glow(wizard.screen, center)


# ─────────────────────────────────────────────────────────────
# Electrocution helpers — operate on a GrimReaper instance
# ─────────────────────────────────────────────────────────────
def grimreaper_electrocute(enemy):
    """Begin the lightning-hit flash sequence on an enemy."""
    enemy.is_electrocuting = True
    enemy.flash_index      = 0
    enemy.flash_timer      = pygame.time.get_ticks()
    enemy._bolt_alpha      = 255
    if GrimReaper.game_ref:
        GrimReaper.game_ref.wizard.is_casting = True


def grimreaper_update_flash(enemy):
    """
    Advance the flash sequence for one enemy.
    Returns True when the sequence is finished (enemy should be removed).
    Also redraws the lightning bolt each frame for a flickering effect.
    """
    if not enemy.is_electrocuting:
        return False

    now = pygame.time.get_ticks()
    if now - enemy.flash_timer >= enemy.flash_interval:
        enemy.flash_index += 1
        enemy.flash_timer  = now

    progress          = enemy.flash_index / max(len(enemy.flash_colors), 1)
    enemy._bolt_alpha = int(255 * (1.0 - progress))

    _grimreaper_draw_bolt(enemy)

    if enemy.flash_index >= len(enemy.flash_colors):
        enemy.is_electrocuting = False
        enemy.flash_index      = len(enemy.flash_colors) - 1
        if GrimReaper.game_ref:
            still_zapping = any(
                g.is_electrocuting
                for g in GrimReaper.all_enemies
                if g is not enemy
            )
            if not still_zapping:
                GrimReaper.game_ref.wizard.is_casting = False
        return True
    return False


def _grimreaper_draw_bolt(enemy):
    """Draw the jagged lightning bolt from the wizard's staff tip to this enemy."""
    if not GrimReaper.game_ref:
        return
    wizard = GrimReaper.game_ref.wizard
    start  = wizard_cast_origin(wizard)
    end    = enemy.rect.center
    draw_lightning_bolt(
        enemy.screen, start, end,
        alpha=max(60, enemy._bolt_alpha)
    )


def grimreaper_blit_flash(enemy):
    """Tint the enemy sprite with the current flash colour."""
    if enemy.flash_index >= len(enemy.flash_colors):
        return
    color  = enemy.flash_colors[enemy.flash_index]
    tinted = enemy.image_gr.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    enemy.screen.blit(tinted, enemy.rect)

# ─────────────────────────────────────────────────────────────
# Base Powers class
# ─────────────────────────────────────────────────────────────
class Powers:
    def __init__(self, game):
        self.game     = game
        self.wizard   = game.wizard
        self.settings = game.settings
        self.screen   = game.screen

        self.glowing        = False
        self.current_radius = 200


# ─────────────────────────────────────────────────────────────
# Dome
# ─────────────────────────────────────────────────────────────
class Dome(Powers):
    def __init__(self, game):
        self.game     = game
        self.wizard   = game.wizard
        self.settings = game.settings
        self.screen   = game.screen

        self.DOME_RADIUS    = 100
        self.DOME_DURATION  = 5000
        self.dome_active    = False
        self.dome_start_time = 0

        self.current_radius = self.DOME_RADIUS

        self.character_color   = (246, 255, 152)
        self.character_outline = (255, 255, 255)

        # Cooldown settings
        self.cooldown       = 5000  # 5 seconds in milliseconds
        self.cooldown_start = 0
        self.on_cooldown    = False
        self.glowing        = False

    def player_glow(self, pos):
        """Render the pulsing dome shield around the wizard."""
        current_time = pygame.time.get_ticks()

        if self.on_cooldown:
            if current_time - self.cooldown_start >= self.cooldown:
                self.on_cooldown = False   # cooldown finished — fall through to draw
            else:
                return                     # still waiting — nothing to draw

        if not self.dome_active:
            return

        if current_time - self.dome_start_time > self.DOME_DURATION:
            self.glowing         = False
            self.dome_active     = False
            self.on_cooldown     = True
            self.cooldown_start  = current_time
            return

        elapsed        = current_time - self.dome_start_time
        pulse          = abs(math.sin(elapsed * 0.005))
        pulse_radius_x = int(150 + 20 * pulse)
        pulse_radius_y = pulse_radius_x
        self.current_radius = pulse_radius_x

        # ── Warning blink as the dome is about to expire ──────────────
        remaining = self.DOME_DURATION - elapsed
        BLINK_WARNING_TIME = 1500   # ms before expiry to start blinking
        dome_alpha = 70
        if remaining <= BLINK_WARNING_TIME:
            # Blink faster the closer it gets to disappearing
            blink_speed = 0.02 + (1 - (remaining / BLINK_WARNING_TIME)) * 0.04
            blink = abs(math.sin(elapsed * blink_speed))
            dome_alpha = int(70 * blink)

        center_x = pos[0]
        center_y = pos[1] - 40

        dome_surface = pygame.Surface(
            (pulse_radius_x * 2, pulse_radius_y), pygame.SRCALPHA)
        pygame.draw.ellipse(
            dome_surface,
            (246, 255, 152, dome_alpha),
            (0, 0, pulse_radius_x * 2, pulse_radius_y * 2)
        )
        self.game.screen.blit(
            dome_surface,
            (center_x - pulse_radius_x, center_y - pulse_radius_y)
        )

# ─────────────────────────────────────────────────────────────
# Thunder Strike
# ─────────────────────────────────────────────────────────────
class ThunderStrike(Powers):
    def __init__(self, game):
        self.game     = game
        self.wizard   = game.wizard
        self.settings = game.settings
        self.screen   = game.screen

        self.speed = 30
        self.width = 60

        # Snap the firing direction at the moment of casting —
        # treat 'front' as 'right' so we always have a clear direction
        wf = game.wizard.facing
        self.facing = 'left' if wf == 'left' else 'right'

        # Fixed cast origin — the bolt starts here and never moves
        origin = wizard_cast_origin(self.wizard)
        self.origin_x = float(origin[0])
        self.origin_y = float(origin[1])

        # Tip starts at the origin and advances each frame
        self.tip_x = self.origin_x
        self.tip_y = self.origin_y

        self.points          = []
        self.flicker_counter = 0
        self.hit_enemies     = set()
        self.spawn_time      = pygame.time.get_ticks()
        self.duration        = 5000
        self.glow_surf       = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        self._generate_lightning()   # build initial zigzag points
        self.alpha = 255

        self.character_color   = (246, 255, 152)
        self.character_outline = (255, 255, 255)

        # Show the cast glow for the life of this strike
        self.wizard.is_casting = True

        # Instantly electrocute every reaper currently on screen
        self.electrocute_all()

    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_time > self.duration

    # ── bolt shape ────────────────────────────────────────────
    def _generate_lightning(self):
        """
        Build a zigzag bolt from the fixed cast origin to the current tip
        position, with random vertical jags for the flickering effect.
        """
        start_x = self.origin_x
        start_y = self.origin_y
        end_x   = self.tip_x
        end_y   = self.origin_y   # bolt travels horizontally

        segments    = 14
        self.points = [(start_x, start_y)]

        for i in range(1, segments):
            t      = i / segments
            mx     = start_x + (end_x - start_x) * t
            my     = start_y + (end_y - start_y) * t
            offset = random.uniform(-18, 18)
            self.points.append((mx, my + offset))

        self.points.append((end_x, end_y))

    # ── per-frame update ──────────────────────────────────────
    def update(self):
        # Advance the tip outward each frame
        if self.facing == 'right':
            self.tip_x = min(self.tip_x + self.speed, self.settings.screen_width)
        else:
            self.tip_x = max(self.tip_x - self.speed, 0)

        # Regenerate zigzag every other frame for the flicker effect
        self.flicker_counter += 1
        if self.flicker_counter % 2 == 0:
            self._generate_lightning()

    # ── drawing ───────────────────────────────────────────────
    def draw(self):
        if len(self.points) < 2:
            return

        # Outer glow (thick, semi-transparent blue/purple)
        glow_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        pygame.draw.lines(glow_surf, (100, 100, 255, 80),
                          False, [(int(p[0]), int(p[1])) for p in self.points], 10)
        self.screen.blit(glow_surf, (0, 0))

        # Mid glow (medium, white-blue)
        pygame.draw.lines(self.screen, (180, 180, 255),
                          False, [(int(p[0]), int(p[1])) for p in self.points], 5)

        # Core (thin, bright white)
        pygame.draw.lines(self.screen, (255, 255, 255),
                          False, [(int(p[0]), int(p[1])) for p in self.points], 2)

        # Sparks at each zigzag point
        for point in self.points[1:-1]:
            spark_length = random.randint(5, 14)
            spark_angle  = random.uniform(0, 2 * math.pi)
            end_x = point[0] + math.cos(spark_angle) * spark_length
            end_y = point[1] + math.sin(spark_angle) * spark_length
            pygame.draw.line(self.screen, (255, 255, 150),
                             (int(point[0]), int(point[1])),
                             (int(end_x), int(end_y)), 1)

    def is_off_screen(self):
        return self.tip_x >= self.settings.screen_width or self.tip_x <= 0

    def expire(self):
        """Call when removing this strike — clears the casting glow if no strikes remain."""
        game = self.game
        still_striking = any(s is not self for s in game.thunder_strikes)
        still_zapping  = any(g.is_electrocuting for g in GrimReaper.all_enemies)
        if not still_striking and not still_zapping:
            self.wizard.is_casting = False

    # ── collision + electrocution ─────────────────────────────
    def electrocute_all(self):
        """
        Called once at spawn time — instantly electrocutes every reaper
        currently on screen.  No travel or line intersection needed.
        """
        for enemy in GrimReaper.all_enemies:
            if enemy not in self.hit_enemies:
                self.hit_enemies.add(enemy)
                grimreaper_electrocute(enemy)