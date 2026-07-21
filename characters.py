import pygame
import os
import random
import math

from settings import Settings

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
SPRITE_SIZE  = (220, 220)   # display size for every character
ANIM_FPS     = 6            # walk-cycle speed (frames per second)
BOB_AMOUNT   = 4            # pixels the sprite bobs up/down while walking
BLACK_THRESH = 30           # sum-of-RGB threshold for background removal

# ─────────────────────────────────────────────────────────────
# Image loader
# ─────────────────────────────────────────────────────────────
def load_image_fast(path, size=SPRITE_SIZE):
    raw = pygame.image.load(path).convert_alpha()
    corner_color = raw.get_at((0, 0))[:3]
    raw.set_colorkey(corner_color)
    surf = pygame.Surface(raw.get_size(), pygame.SRCALPHA)
    surf.blit(raw, (0, 0))
    return pygame.transform.smoothscale(surf, size)


# ─────────────────────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────────────────────
class Characters:
    def __init__(self, game):
        self.screen      = game.screen
        self.screen_rect = game.screen.get_rect()
        self.settings    = game.settings

        self.moving_right = False
        self.moving_left  = False
        self.moving_up    = False
        self.moving_down  = False

    def burst(self):
        """Burst effect when an enemy is killed by the dome."""
        for radius in range(20, 100, 20):
            pygame.draw.circle(self.screen, (255, 165, 0),
                               self.rect.center, radius, 5)
        pygame.display.flip()
        pygame.time.delay(50)


# ─────────────────────────────────────────────────────────────
# Wizard  (player)
# ─────────────────────────────────────────────────────────────
class Wizard(Characters):
    def __init__(self, game):
        super().__init__(game)

        base = os.path.dirname(__file__)
        p    = lambda f: os.path.join(base, 'photos', f)

        img_right    = load_image_fast(p('wiz_right(1).png'))
        img_left     = load_image_fast(p('wiz_left(1).png'))
        img_semileft = load_image_fast(p('wiz_semileft(1).png'))
        img_front    = load_image_fast(p('wiz_front(1).png'))

        img_semi_right        = pygame.transform.flip(img_semileft, True, False)
        self.frames_right     = [img_right, img_semi_right]
        self.frames_left      = [img_left,  img_semileft]
        self.frame_idle       = img_front

        # Animation state
        self.frame_index  = 0
        self.anim_timer   = 0.0
        self.frame_delay  = 1.0 / ANIM_FPS
        self.bob_timer    = 0.0
        self.bob_offset   = 0

        self.is_moving    = False
        self.facing       = 'front'   # 'right' | 'left' | 'front'

        # Casting state — read by powers.py to render the staff-tip glow.
        # x is the horizontal centre; wizard_cast_origin() shifts it left/right
        # based on facing so the bolt starts from the staff tip.
        self.is_casting       = False
        self.cast_hand_offset = (SPRITE_SIZE[0] // 2, 30)  # (centre-x, staff-tip y)

        self.wizard_image = self.frame_idle
        self.rect = self.wizard_image.get_rect(
            midbottom=(self.settings.screen_width  // 2,
                       self.settings.screen_height - 130)
        )
        self.base_y = self.rect.y

    # ── animation tick ────────────────────────────────────────
    def update_animation(self, dt):
        if not self.is_moving:
            self.frame_index  = 0
            self.anim_timer   = 0.0
            self.bob_offset   = 0
            self.wizard_image = self.frame_idle
            return

        frames = (self.frames_right if self.facing == 'right'
                  else self.frames_left)

        self.anim_timer += dt
        if self.anim_timer >= self.frame_delay:
            self.anim_timer  -= self.frame_delay
            self.frame_index  = (self.frame_index + 1) % len(frames)

        self.bob_timer  += dt
        self.bob_offset  = int(math.sin(self.bob_timer * ANIM_FPS * math.pi)
                               * BOB_AMOUNT)

        self.wizard_image = frames[self.frame_index]

    # ── movement ──────────────────────────────────────────────
    def update(self, dt=0.016):
        speed = 5
        moved = False

        if self.moving_right:
            self.rect.x += speed
            self.facing  = 'right'
            moved        = True
        if self.moving_left:
            self.rect.x -= speed
            self.facing  = 'left'
            moved        = True

        self.rect.x = max(0, min(self.rect.x,
                                 self.screen_rect.width - self.rect.width))

        self.is_moving = moved
        if not moved:
            self.facing = 'front'

        self.update_animation(dt)
        self.rect.y = self.base_y + self.bob_offset

    def blit_wizard(self):
        self.screen.blit(self.wizard_image, self.rect)


# ─────────────────────────────────────────────────────────────
# Grim Reaper  (enemy)
# ─────────────────────────────────────────────────────────────
class GrimReaper(Characters):
    all_enemies  = []
    spawn_timer  = 0
    spawn_delay  = 3000          # one new Grim Reaper every 3 seconds
    game_ref     = None
    speed        = 3

    @classmethod
    def increase_speed(cls):
        cls.speed += 0.5

    def __init__(self, game):
        super().__init__(game)
        self.wizard = game.wizard

        base = os.path.dirname(__file__)
        p    = lambda f: os.path.join(base, 'photos', f)

        img_right = load_image_fast(p('gr_right.png'))
        img_left  = load_image_fast(p('gr_left.png'))
        img_front = load_image_fast(p('gr_front.png'))

        img_right_alt = pygame.transform.smoothscale(
            img_right,
            (int(SPRITE_SIZE[0] * 0.95), int(SPRITE_SIZE[1] * 0.97)))
        img_right_alt = pygame.transform.smoothscale(img_right_alt, SPRITE_SIZE)

        img_left_alt  = pygame.transform.smoothscale(
            img_left,
            (int(SPRITE_SIZE[0] * 0.95), int(SPRITE_SIZE[1] * 0.97)))
        img_left_alt  = pygame.transform.smoothscale(img_left_alt, SPRITE_SIZE)

        self.frames_right = [img_right, img_right_alt]
        self.frames_left  = [img_left,  img_left_alt]
        self.frame_front  = img_front

        # Animation state
        self.frame_index  = 0
        self.anim_timer   = 0.0
        self.frame_delay  = 1.0 / ANIM_FPS
        self.bob_timer    = 0.0
        self.bob_offset   = 0
        self.facing       = 'right'

        # Electrocution state — driven by powers.py
        self.is_electrocuting = False
        self.flash_index      = 0
        self.flash_timer      = 0
        self.flash_interval   = 40          # ms between flash steps
        self.flash_colors     = [
            (100, 100, 255), (255, 255, 255),
            (50,  50,  200), (255, 255, 255),
            (0,   0,   150), (255, 255, 255),
        ]
        self._bolt_alpha = 255

        GrimReaper.game_ref = game

        self.image_gr = self.frames_right[0]
        self.rect     = self.image_gr.get_rect()

        self.grim_reaper_x = float(self.rect.x)
        self.grim_reaper_y = float(self.rect.y)

        self.spawn()
        GrimReaper.all_enemies.append(self)

    # ── spawn ─────────────────────────────────────────────────
    def spawn(self):
        side = random.choice(['left', 'right'])
        if side == 'left':
            self.grim_reaper_x = -self.rect.width
            self.facing        = 'right'
        else:
            self.grim_reaper_x = self.settings.screen_width
            self.facing        = 'left'

        self.last_side     = side
        self.grim_reaper_y = self.wizard.rect.y
        self.grim_reaper_y = max(0, min(self.grim_reaper_y,
                                        self.settings.screen_height - self.rect.height))
        self.rect.x = int(self.grim_reaper_x)
        self.rect.y = int(self.grim_reaper_y)

    # ── animation tick ────────────────────────────────────────
    def update_animation(self, dt, dx):
        if abs(dx) > 0.3:
            self.facing = 'right' if dx > 0 else 'left'

        frames = (self.frames_right if self.facing == 'right'
                  else self.frames_left)

        self.anim_timer += dt
        if self.anim_timer >= self.frame_delay:
            self.anim_timer  -= self.frame_delay
            self.frame_index  = (self.frame_index + 1) % len(frames)

        self.bob_timer  += dt
        self.bob_offset  = int(math.sin(self.bob_timer * ANIM_FPS * math.pi)
                               * BOB_AMOUNT)

        self.image_gr = frames[self.frame_index]

    # ── movement ──────────────────────────────────────────────
    def update(self, dt=0.016):
        dx = self.wizard.rect.centerx - self.grim_reaper_x
        dy = self.wizard.rect.centery - self.grim_reaper_y

        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist != 0:
            dx /= dist
            dy /= dist

        self.grim_reaper_x += dx * GrimReaper.speed
        self.grim_reaper_y += dy * GrimReaper.speed

        self.grim_reaper_x = max(-self.rect.width,
                                 min(self.grim_reaper_x,
                                     self.settings.screen_width + self.rect.width))
        self.grim_reaper_y = max(0, min(self.grim_reaper_y,
                                        self.settings.screen_height - 190))

        self.rect.x = int(self.grim_reaper_x)
        self.rect.y = int(self.grim_reaper_y) + self.bob_offset

        self.update_animation(dt, dx)

    # ── spawn check (class-level) ─────────────────────────────
    @classmethod
    def check_spawn(cls):
        current_time = pygame.time.get_ticks()
        if cls.spawn_timer == 0:
            cls.spawn_timer = current_time
        if current_time - cls.spawn_timer >= cls.spawn_delay:
            if cls.game_ref is not None:
                GrimReaper(cls.game_ref)
                cls.spawn_timer = current_time

    # ── update + draw all ─────────────────────────────────────
    @classmethod
    def update_all(cls, dome_pos, dome_radius, dome_active,
                   show_grimreaper=False, dt=0.016):
        # Spawn new reapers on a timer (only while game is running)
        if show_grimreaper:
            if cls.game_ref and not cls.game_ref.game_over_active:
                GrimReaper.check_spawn()

        # Update position and draw every existing reaper
        for grim in cls.all_enemies[:]:

            # Dome collision
            if dome_active:
                distance = math.sqrt(
                    (grim.rect.centerx - dome_pos[0]) ** 2 +
                    (grim.rect.centery - (dome_pos[1] - 40)) ** 2
                )

                if distance <= dome_radius + grim.rect.width // 2:

                    grim.burst()

                    cls.all_enemies.remove(grim)

                    cls.game_ref.enemies_killed += 1

                    if cls.game_ref.enemies_killed % 5 == 0:
                        cls.increase_speed()

                    continue

            if not grim.is_electrocuting:
                grim.update(dt)

            grim.blit_enemy()

    def blit_enemy(self):
        self.screen.blit(self.image_gr, self.rect)