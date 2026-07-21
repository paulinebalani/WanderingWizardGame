import pygame
import math
#import as_
#import as_pd

# — Colour palette ————————————————————————————————————————————————————————————
C_BORDER        = (120,  80, 200)   # vivid purple border
C_BORDER_LIT    = (200, 160, 255)   # bright highlight on hover/press
C_BTN_IDLE      = ( 30,  20,  70)   # deep purple fill
C_BTN_HOVER     = ( 60,  40, 130)
C_BTN_PRESS     = (100,  60, 180)
C_TEXT_MAIN     = (220, 200, 255)   # lavender white
C_TEXT_ACCENT   = (255, 220, 100)   # golden yellow
C_TEXT_DIM      = (140, 120, 200)   # dim purple
C_QUIT_IDLE     = ( 60,  10,  20)
C_QUIT_HOVER    = (120,  20,  40)
C_BACK_IDLE     = ( 20,  40,  80)
C_BACK_HOVER    = ( 40,  80, 140)
C_PANEL         = ( 18,  14,  45)   # dialog panel

# —— Forest / background-matching pixel palette ——————————————————————————————
# These match the dark forest bg: deep greens, midnight blues, mossy shadows
C_PIX_DARK      = (  8,  18,  12)   # near-black forest shadow
C_PIX_MID       = ( 18,  42,  28)   # deep forest green
C_PIX_LIGHT     = ( 34,  72,  48)   # mid moss green
C_PIX_EDGE      = ( 55, 110,  70)   # lighter forest edge
C_PIX_GLOW      = ( 90, 200, 110)   # magical green glow / highlight
C_PIX_GOLD      = (210, 175,  60)   # rune/accent gold
C_PIX_PURPLE    = ( 80,  40, 140)   # arcane purple accent
C_PIX_TEXT      = (220, 240, 210)   # bright parchment text
C_PIX_SHADOW    = (  0,   0,   0, 120)  # drop shadow (RGBA)

# Parchment scroll palette  (warm tan, matching reference image)
C_SCROLL_PARCH  = (240, 210, 160)   # inner parchment fill
C_SCROLL_EDGE   = (180, 130,  70)   # darker tan border band
C_SCROLL_DARK   = ( 50,  30,   5)   # outline / pixel corners
C_SCROLL_SHADE  = (200, 165, 105)   # inner shadow band
C_SCROLL_TEXT   = ( 40,  20,   0)   # dark ink text on parchment


def _pixel_font(size):
    for name in ("Courier New", "Courier", "monospace"):
        try:
            f = pygame.font.SysFont(name, size, bold=True)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.Font(None, size)


# ——————————————————————————————————————————————————————————————————————————————
# PixelScrollButton  – forest-themed pixel-art scroll button with float anim
# ——————————————————————————————————————————————————————————————————————————————

# Global timer so all buttons share one phase clock
_start_ticks = pygame.time.get_ticks if pygame else 0

FLOAT_AMPLITUDE = 4      # pixels up/down
FLOAT_SPEED     = 0.0018  # radians per ms  (one full cycle ≈ 3.5 s)
PIXEL_SIZE      = 4       # size of one "pixel block" in the border art


def _now_ms():
    return pygame.time.get_ticks()


def draw_pixel_forest_button(surface, rect, text, font,
                              hovered=False, pressed=False,
                              float_offset=0, accent_color=None):
    """
    Draw a pixel-art forest-themed button.

    Visual layers (back → front):
      1. Drop shadow
      2. Dark outer pixel border (chunky, 8-bit style)
      3. Mid-green body fill
      4. Lighter inner bevel (top-left edges)
      5. Darker inner bevel (bottom-right edges)
      6. Corner "pixel nubs" (2×2 accent squares)
      7. Scanline texture (subtle alternating rows)
      8. Hover/press glow overlay
      9. Text with drop shadow
    """
    if accent_color is None:
        accent_color = C_PIX_GLOW

    x, y, w, h = rect.x, rect.y + float_offset, rect.w, rect.h
    S = PIXEL_SIZE

    # —— brightness helpers ——————————————————————————————————————————————
    def _tint(color, delta):
        return tuple(max(0, min(255, c + delta)) for c in color[:3])

    body       = C_BTN_IDLE
    bevel_hi   = C_BORDER_LIT
    bevel_lo   = C_BORDER
    border_col = C_BORDER
    glow_col   = accent_color
    text_col   = C_TEXT_MAIN

    if pressed:
        body     = _tint(C_BTN_IDLE,  -10)
        bevel_hi = C_BTN_IDLE
        bevel_lo = C_BORDER_LIT
        glow_col = _tint(accent_color, 40)
        float_offset = 2        # squish down
    elif hovered:
        body     = _tint(C_BORDER_LIT,  10)
        glow_col = _tint(accent_color, 20)
        text_col = C_PIX_GOLD

    # 1. Drop shadow (offset 4px, semi-transparent)
    shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, 0))
    pygame.draw.rect(shadow_surf, (0, 0, 0, 100), (0, 0, w, h))
    surface.blit(shadow_surf, (x + S, y + S))

    # 2. Chunky outer border  (2×S thick)
    border_thick = S * 2
    pygame.draw.rect(surface, border_col,
                     pygame.Rect(x, y, w, h))

    # 3. Body fill  (inset by border_thick)
    body_rect = pygame.Rect(x + border_thick, y + border_thick,
                            w - border_thick * 2, h - border_thick * 2)
    pygame.draw.rect(surface, body, body_rect)

    # 4. Top-left bevel highlight (1×S)
    # top edge
    pygame.draw.rect(surface, bevel_hi,
                     pygame.Rect(x + border_thick, y + border_thick,
                                 w - border_thick * 2, S))
    # left edge
    pygame.draw.rect(surface, bevel_hi,
                     pygame.Rect(x + border_thick, y + border_thick,
                                 S, h - border_thick * 2))

    # 5. Bottom-right bevel shadow (1×S)
    pygame.draw.rect(surface, bevel_lo,
                     pygame.Rect(x + border_thick, y + h - border_thick - S,
                                 w - border_thick * 2, S))
    pygame.draw.rect(surface, bevel_lo,
                     pygame.Rect(x + w - border_thick - S, y + border_thick,
                                 S, h - border_thick * 2))

    # 6. Corner pixel nubs (2S × 2S accent squares at all four corners)
    corners = [
        (x,             y),
        (x + w - S*2,   y),
        (x,             y + h - S*2),
        (x + w - S*2,   y + h - S*2),
    ]
    for cx2, cy2 in corners:
        pygame.draw.rect(surface, C_PIX_EDGE, pygame.Rect(cx2, cy2, S*2, S*2))

    # 7. Subtle scanlines (every 2*S rows, alpha overlay)
    scanline_surf = pygame.Surface((w - border_thick*2, h - border_thick*2),
                                   pygame.SRCALPHA)
    for row in range(0, scanline_surf.get_height(), S * 2):
        pygame.draw.rect(scanline_surf, (0, 0, 0, 25),
                         pygame.Rect(0, row, scanline_surf.get_width(), S))
    surface.blit(scanline_surf, (x + border_thick, y + border_thick))

    # 8. Hover / press glow overlay
    if hovered or pressed:
        glow_surf = pygame.Surface((w - border_thick*2, h - border_thick*2),
                                   pygame.SRCALPHA)
        alpha = 60 if pressed else 35
        glow_surf.fill((*glow_col[:3], alpha))
        surface.blit(glow_surf, (x + border_thick, y + border_thick))

        # glow outline (inner border redrawn in glow colour)
        pygame.draw.rect(surface, glow_col,
                         pygame.Rect(x + border_thick, y + border_thick,
                                     w - border_thick*2, h - border_thick*2),
                         width=S)

    # 9. Text with drop shadow
    text_surf = font.render(text, True, text_col)
    text_rect = text_surf.get_rect(center=(x + w // 2, y + h // 2))

    shadow_text = font.render(text, True, (0, 0, 0))
    surface.blit(shadow_text, text_rect.move(2, 2))
    surface.blit(text_surf,   text_rect)


# ——————————————————————————————————————————————————————————————————————————————
# PixelForestButton – event-aware wrapper with floating animation
# ——————————————————————————————————————————————————————————————————————————————

class PixelForestButton:
    """
    Pixel-art forest button with sinusoidal float animation.
    Drop-in replacement for ScrollButton in all menu classes.
    """

    def __init__(self, screen, text, rect, font_size=52,
                 phase_offset=0.0, accent_color=None):
        self.screen       = screen
        self.text         = text
        self.rect         = pygame.Rect(rect)
        self.font         = _pixel_font(font_size)
        self._state       = "idle"
        self._phase       = phase_offset   # radians, so buttons float at diff times
        self._accent      = accent_color or C_PIX_GLOW

    def _float_offset(self):
        t = _now_ms()
        return int(math.sin(t * FLOAT_SPEED + self._phase) * FLOAT_AMPLITUDE)

    def update(self, mouse_pos, mouse_down):
        if self.rect.collidepoint(mouse_pos):
            self._state = "press" if mouse_down else "hover"
        else:
            self._state = "idle"

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONUP and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self):
        draw_pixel_forest_button(
            self.screen, self.rect, self.text, self.font,
            hovered =(self._state == "hover"),
            pressed =(self._state == "press"),
            float_offset=self._float_offset(),
            accent_color=self._accent,
        )


# Keep ScrollButton as an alias so existing code still works
ScrollButton = PixelForestButton


# ——————————————————————————————————————————————————————————————————————————————
# PixelButton  – small plain pixel button (kept for dialogs & nav)
# ——————————————————————————————————————————————————————————————————————————————

class PixelButton:
    def __init__(self, screen, text, rect,
                 font_size=44,
                 idle_color=C_PIX_MID,
                 hover_color=C_BORDER_LIT,
                 press_color=C_PIX_EDGE,
                 border_color=C_BTN_IDLE,
                 text_color=C_PIX_TEXT):
        self.screen       = screen
        self.text         = text
        self.rect         = pygame.Rect(rect)
        self.idle_color   = idle_color
        self.hover_color  = hover_color
        self.press_color  = press_color
        self.border_color = border_color
        self.text_color   = text_color
        self.font         = _pixel_font(font_size)
        self._state       = "idle"
        self._render_text()

    def _render_text(self):
        self._surf      = self.font.render(self.text, True, self.text_color)
        self._surf_rect = self._surf.get_rect(center=self.rect.center)

    def update(self, mouse_pos, mouse_down):
        if self.rect.collidepoint(mouse_pos):
            self._state = "press" if mouse_down else "hover"
        else:
            self._state = "idle"

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONUP and event.button == 1
                and self.rect.collidepoint(event.pos))

    @property
    def _fill(self):
        return {"idle": self.idle_color,
                "hover": self.hover_color,
                "press": self.press_color}[self._state]

    @property
    def _border(self):
        return C_PIX_GLOW if self._state != "idle" else self.border_color

    def draw(self):
        S = PIXEL_SIZE
        x, y, w, h = self.rect
        pygame.draw.rect(self.screen, self.border_color, self.rect)
        inner = self.rect.inflate(-S*2, -S*2)
        pygame.draw.rect(self.screen, self._fill, inner)
        pygame.draw.rect(self.screen, self._border, self.rect, width=S)
        # corner nubs
        for cx2, cy2 in [(x, y), (x+w-S*2, y), (x, y+h-S*2), (x+w-S*2, y+h-S*2)]:
            pygame.draw.rect(self.screen, C_PIX_EDGE, pygame.Rect(cx2, cy2, S*2, S*2))
        shadow = self.font.render(self.text, True, (0, 0, 0))
        self.screen.blit(shadow, self._surf_rect.move(2, 2))
        self.screen.blit(self._surf, self._surf_rect)


# ——————————————————————————————————————————————————————————————————————————————
# Original Button  (backward-compat, used by wandering_wizard play button)
# ——————————————————————————————————————————————————————————————————————————————

class Button:
    def __init__(self, ai_game, msg):
        self.screen       = ai_game.screen
        self.screen_rect  = self.screen.get_rect()
        self.width, self.height = 300, 80
        self.button_color = (30, 20, 70)
        self.text_color   = (220, 200, 255)
        self.font         = _pixel_font(52)
        self.rect         = pygame.Rect(0, 0, self.width, self.height)
        self.rect.centerx = self.screen_rect.centerx
        self.rect.centery = self.screen_rect.centery
        self._prep_msg(msg)

    def _prep_msg(self, msg):
        self.msg_image      = self.font.render(msg, True,
                                               self.text_color,
                                               self.button_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def draw_button(self):
        S = PIXEL_SIZE
        x, y, w, h = self.rect
        pygame.draw.rect(self.screen, C_BTN_IDLE, self.rect)
        inner = self.rect.inflate(-S*2, -S*2)
        pygame.draw.rect(self.screen, self.button_color, inner)
        for cx2, cy2 in [(x, y), (x+w-S*2, y), (x, y+h-S*2), (x+w-S*2, y+h-S*2)]:
            pygame.draw.rect(self.screen, C_PIX_EDGE, pygame.Rect(cx2, cy2, S*2, S*2))
        self.screen.blit(self.msg_image, self.msg_image_rect)


# ——————————————————————————————————————————————————————————————————————————————
# TypewriterText  (unchanged – kept for HowToPlay)
# ——————————————————————————————————————————————————————————————————————————————

class TypewriterText:
    SPEED = 2

    def __init__(self, full_text, font, color, max_width, x, y):
        self.full_text  = full_text
        self.font       = font
        self.color      = color
        self.max_width  = max_width
        self.x          = x
        self.y          = y
        self._pos       = 0
        self._done      = False
        self._wrap(full_text) 
        #self._lines     = self._wrap(full_text)
        self._total_chars()
        self._line_h    = font.get_height() + 6

    def _wrap(self, text):
        self.lines = []
    
        # If a list of sentences was passed, process them one by one
        if isinstance(text, (tuple, list)):
            paragraphs = text
        else:
            # Fallback if it's a single string with \n characters
            paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            words = paragraph.split(' ')
            current = ''
        
            for word in words:
                test = f"{current} {word}".strip() if current else word
            
                # Check if word fits on current line
                if self.font.size(test)[0] <= self.max_width:
                    current = test
                else:
                    if current:
                        self.lines.append(current)
                    current = word
                
            if current:
                self.lines.append(current)
            
    def _total_chars(self):
        # Calculates the character count and stores it directly on the object
        # Uses self.lines (populated by your updated _wrap method)
        self.total_chars_count = sum(len(line) for line in self.lines) + len(self.lines)
    
    def update(self):
        # Instead of total = self._total_chars(), read the variable directly:
        if self._pos < self.total_chars_count:
            self._pos = min(self._pos + self.SPEED, self.total_chars_count)
        else:
            self._done = True

    def skip(self):
        # Read the variable directly here as well:
        self._pos = self.total_chars_count
        self._done = True

    @property
    def done(self):
        return self._done

    def draw(self, surface):
        remaining = self._pos
        for i, line in enumerate(self.lines):
            chars   = min(remaining, len(line))
            partial = line[:chars]
            if partial:
                surf = self.font.render(partial, True, self.color)
                surface.blit(surf, (self.x, self.y + i * self._line_h))
            remaining -= chars + 1
            if remaining < 0:
                break

    @property
    def height(self):
        return len(self.lines) * self._line_h


# ——————————————————————————————————————————————————————————————————————————————
# MainMenu
# ——————————————————————————————————————————————————————————————————————————————

class MainMenu:
    """
    handle_event() → 'start' | 'how_to_play' | 'credits' | 'quit_confirm' | None
    """

    def __init__(self, screen):
        self.screen = screen
        sw, sh = screen.get_size()

        btn_w, btn_h = 320, 56
        cx = sw // 2
        # Position buttons in the lower half, below where the title art sits
        top  = int(sh * 0.58)
        gap  = btn_h + 18

        # Each button gets a different phase so they float out of sync
        self.btn_start   = PixelForestButton(screen, "START",
                               (cx - btn_w // 2, top,              btn_w, btn_h), 38,
                               phase_offset=0.0,   accent_color=C_PIX_GLOW)
        self.btn_how     = PixelForestButton(screen, "HOW TO PLAY",
                               (cx - btn_w // 2, top + gap,        btn_w, btn_h), 32,
                               phase_offset=1.1,   accent_color=C_PIX_GOLD)
        self.btn_credits = PixelForestButton(screen, "CREDITS",
                               (cx - btn_w // 2, top + gap*2,      btn_w, btn_h), 32,
                               phase_offset=2.2,   accent_color=C_PIX_PURPLE)
        self.btn_settings = PixelForestButton(screen, "SETTINGS",
                               (cx - btn_w // 2, top + gap*3,      btn_w, btn_h), 32,
                               phase_offset=3.3,   accent_color=(100, 180, 255))
        self.btn_quit    = PixelForestButton(screen, "QUIT",
                               (cx - btn_w // 2, top + gap*4,      btn_w, btn_h), 32,
                               phase_offset=4.4,   accent_color=(180, 60, 60))

        self._buttons = [self.btn_start, self.btn_how,
                         self.btn_credits, self.btn_settings, self.btn_quit]

    def handle_event(self, event):
        if self.btn_start.is_clicked(event):    return 'start'
        if self.btn_how.is_clicked(event):      return 'how_to_play'
        if self.btn_credits.is_clicked(event):  return 'credits'
        if self.btn_quit.is_clicked(event):     return 'quit_confirm'
        if self.btn_settings.is_clicked(event): return 'settings'
        return None

    def update(self, mouse_pos, mouse_down):
        for b in self._buttons:
            b.update(mouse_pos, mouse_down)

    def draw(self):
        # No overlay – background is drawn by wandering_wizard.py before calling this
        for b in self._buttons:
            b.draw()


# ——————————————————————————————————————————————————————————————————————————————
# QuitConfirm
# ——————————————————————————————————————————————————————————————————————————————

class QuitConfirm:
    """handle_event() → 'yes' | 'no' | None"""

    def __init__(self, screen):
        self.screen = screen
        sw, sh = screen.get_size()

        self.q_font = _pixel_font(40)

        box_w, box_h = 560, 240
        self.box_rect = pygame.Rect((sw - box_w) // 2, (sh - box_h) // 2,
                                    box_w, box_h)
        bx, by = self.box_rect.x, self.box_rect.y

        self.btn_yes = PixelForestButton(screen, "YES",
                           (bx + 50,              by + box_h - 90, 180, 62), 38,
                           phase_offset=0.0, accent_color=C_PIX_GLOW)
        self.btn_no  = PixelForestButton(screen, "NO",
                           (bx + box_w - 230,     by + box_h - 90, 180, 62), 38,
                           phase_offset=1.6, accent_color=(180, 60, 60))

        self._overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))

    def handle_event(self, event):
        if self.btn_yes.is_clicked(event): return 'yes'
        if self.btn_no.is_clicked(event):  return 'no'
        return None

    def update(self, mouse_pos, mouse_down):
        self.btn_yes.update(mouse_pos, mouse_down)
        self.btn_no.update(mouse_pos, mouse_down)

    def draw(self):
        self.screen.blit(self._overlay, (0, 0))
        S = PIXEL_SIZE
        # Panel
        pygame.draw.rect(self.screen, C_PIX_DARK,  self.box_rect)
        inner = self.box_rect.inflate(-S*4, -S*4)
        pygame.draw.rect(self.screen, C_PIX_MID,   inner)
        pygame.draw.rect(self.screen, C_PIX_EDGE,  self.box_rect, width=S*2)

        lines = ["Are you sure you", "want to quit?"]
        for i, line in enumerate(lines):
            surf = self.q_font.render(line, True, C_PIX_TEXT)
            rect = surf.get_rect(centerx=self.box_rect.centerx,
                                 top=self.box_rect.top + 28 + i * 48)
            self.screen.blit(surf, rect)

        self.btn_yes.draw()
        self.btn_no.draw()


# ——————————————————————————————————————————————————————————————————————————————
# HowToPlay
# ——————————————————————————————————————————————————————————————————————————————

_HOW_TO_PLAY_PAGES = [
    ("THE STORY",
     "While searching for an ancient magical knowledge, a wizard accidentally entered a cursed forest "
     "and became trapped by a powerful barrier."),
    ("OBJECTIVE",
     "To survive, the wizard must defeat enemies using powerful "
     "magic while avoiding their deadly touch."),
    ("CONTROLS", [
        "- Move left and right using the Arrow Keys.",
        "- Press 'D' to activate the Magical Dome for protection.",
        "- The Magical Dome has a 5-second cooldown after each use.",
        "- Press 'A' to cast a Lightning Strike against approaching enemies.",
        "- Lightning Strike has a 10-second cooldown after each use."
    ]),
    ("CHALLENGE",
     "The game challenges players to kill as many grim reapers as possible "
     "in the dark and dangerous forest where vision decreases and grim reapers grow faster over time."),
]


class HowToPlay:
    """handle_event() → 'main_menu' | None"""

    def __init__(self, screen):
        self.screen  = screen
        sw, sh       = screen.get_size()
        self._page   = 0
        self._tw     = None

        # Semi-transparent dark bg so the game bg still shows subtly
        self._bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._bg.fill((5, 8, 28, 230))

        self.title_font = _pixel_font(70)    # large title
        self.body_font  = _pixel_font(50)    # large body
        self.nav_font   = _pixel_font(32)

        margin        = 100
        self._text_w  = sw - margin * 2
        self._text_x  = margin

        # Title sits near top  (~12 % down)
        self._title_y = int(sh * 0.12)
        # Body text starts ~28 % down, leaving room below title
        self._body_y  = int(sh * 0.30)

        # — nav buttons ——————————————————————————————————————————————————
        btn_w, btn_h = 220, 68
        bot = sh - btn_h - 36

        self.btn_back = PixelForestButton(screen, "< BACK",
                            (36, bot, btn_w, btn_h), 34,
                            phase_offset=0.0)
        self.btn_next = PixelForestButton(screen, "NEXT >",
                            (sw - btn_w - 36, bot, btn_w, btn_h), 34,
                            phase_offset=1.2)
        self.btn_menu = PixelForestButton(screen, "< MENU",
                            (20, 20, 200, 62), 30,
                            phase_offset=2.4)

        self._load_page()

    def _load_page(self):
        # Grab the body text string from your _HOW_TO_PLAY_PAGES tuple
        body_text = _HOW_TO_PLAY_PAGES[self._page][1]
    
        #Check if body_text is a list (like Option 2 for Controls sentences)
        # If it's a list, join it with newlines so the text wrapper parses it cleanly
        if isinstance(body_text, list):
            body_text = "\n".join(body_text)
        
        # Instantiate TypewriterText matching its exact __init__ signature:
        # def __init__(self, full_text, font, color, max_width, x, y):
        self._tw = TypewriterText(
            body_text, self.body_font, C_PIX_TEXT, self._text_w, self._text_x, self._body_y)

    def handle_event(self, event):
        if self.btn_menu.is_clicked(event):
            return 'main_menu'

        if self.btn_back.is_clicked(event):
            if self._page > 0:
                self._page -= 1
                self._load_page()

        if self.btn_next.is_clicked(event):
            if not self._tw.done:
                # First press skips typewriter
                self._tw.skip()
            elif self._page < len(_HOW_TO_PLAY_PAGES) - 1:
                self._page += 1
                self._load_page()
            else:
                # Last page + typewriter done → back to main menu
                return 'main_menu'

        return None

    def update(self, mouse_pos, mouse_down):
        self._tw.update()
        self.btn_back.update(mouse_pos, mouse_down)
        self.btn_next.update(mouse_pos, mouse_down)
        self.btn_menu.update(mouse_pos, mouse_down)

    def draw(self):
        sw = self.screen.get_width()
        self.screen.blit(self._bg, (0, 0))

        # — Title at upper-centre ————————————————————————————————————————
        title_text = _HOW_TO_PLAY_PAGES[self._page][0]
        t_surf = self.title_font.render(title_text, True, C_PIX_GOLD)
        # shadow
        sh_surf = self.title_font.render(title_text, True, (30, 10, 60))
        t_rect  = t_surf.get_rect(centerx=sw // 2, top=self._title_y)
        self.screen.blit(sh_surf, t_rect.move(3, 3))
        self.screen.blit(t_surf,  t_rect)

        # — Body typewriter ——————————————————————————————————————————————
        self._tw.draw(self.screen)

        # — Page indicator ————————————————————————————————————————————————
        last    = self._page == len(_HOW_TO_PLAY_PAGES) - 1
        pg_text = (f"{self._page + 1} / {len(_HOW_TO_PLAY_PAGES)}"
                   + (" | NEXT → MENU" if last and self._tw.done else ""))
        pg_surf = self.nav_font.render(pg_text, True, C_PIX_TEXT)
        pg_rect = pg_surf.get_rect(centerx=sw // 2,
                                   bottom=self.btn_back.rect.top - 12)
        self.screen.blit(pg_surf, pg_rect)

        self.btn_back.draw()
        self.btn_next.draw()
        self.btn_menu.draw()


# ——————————————————————————————————————————————————————————————————————————————
# Credits
# ——————————————————————————————————————————————————————————————————————————————

_CREDITS_TEXT = [
    ("CREDITS",              True),
    ("",                     False),
    ("Game Developer",       True),
    ("Precious Pauline Balani",           False),
    ("",                     True),
    ("Art & Visuals",        True),
    ("Created using Pygame assets and custom designs", False),
    ("Canva", False),
    ("pexels.com", False),
    ("",                     True),
    ("Sound Effects and Music",        True),
    ("Sound Effects from freesound.org",         False),
    ("",                     False), 
    ("Built With",           True),
    ("Python",               False),
    ("Pygame",               False),
    ("",                     True),
    ("Thank You for Playing!", False),
]

class Credits:
    """handle_event() → 'main_menu' | None"""

    SCROLL_SPEED = 1.5

    def __init__(self, screen):
        self.screen      = screen
        sw, sh           = screen.get_size()
        self._bg         = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._bg.fill((5, 8, 28, 215))
        self._sw, self._sh = sw, sh

        self.sub_font  = _pixel_font(34)
        self.name_font = _pixel_font(44)

        self.btn_menu = PixelForestButton(screen, "< MENU",
                            (20, 20, 200, 62), 30,
                            phase_offset=0.0)

        self._scroll_y = float(sh)
        self._auto     = True

    def _line_h(self, is_accent):
        return (self.name_font.get_height() if is_accent
                else self.sub_font.get_height()) + 10

    def handle_event(self, event):
        if self.btn_menu.is_clicked(event):
            return 'main_menu'
        if event.type == pygame.MOUSEWHEEL:
            self._scroll_y -= event.y * 35
            self._auto      = False
        return None

    def update(self, mouse_pos, mouse_down):
        self.btn_menu.update(mouse_pos, mouse_down)
        if self._auto:
            self._scroll_y -= self.SCROLL_SPEED

    def draw(self):
        self.screen.blit(self._bg, (0, 0))
        sw = self._sw

        y = self._scroll_y
        for text, is_accent in _CREDITS_TEXT:
            if not text:
                y += 22
                continue
            font  = self.name_font if is_accent else self.sub_font
            color = C_PIX_GOLD    if is_accent else C_PIX_TEXT
            surf  = font.render(text, True, color)
            rect  = surf.get_rect(centerx=sw // 2, top=int(y))
            if -rect.height < rect.top < self._sh + rect.height:
                self.screen.blit(surf, rect)
            y += self._line_h(is_accent)

        self.btn_menu.draw()

class GameOver:
    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()

        # Match scoreboard font
        self.font_title = pygame.font.SysFont("couriernew", 72, bold=True)
        self.font_btn   = pygame.font.SysFont("couriernew", 30, bold=True)
        self.font_sub   = pygame.font.SysFont("couriernew", 20, bold=True)

        cx = self.screen_rect.centerx
        cy = self.screen_rect.centery

        # Yes button
        self.yes_rect  = pygame.Rect(0, 0, 200, 60)
        self.yes_rect.center = (cx - 130, cy + 80)

        # Quit button
        self.quit_rect = pygame.Rect(0, 0, 200, 60)
        self.quit_rect.center = (cx + 130, cy + 80)

        self.yes_hovered  = False
        self.quit_hovered = False

        # Match scoreboard color palette
        self.color_high    = (255, 140, 0)      # orange - best score
        self.color_current = (180, 210, 255)    # light blue - score
        self.color_label   = (120, 150, 200)    # muted blue - labels
        self.color_shadow  = (10,  20,  40)     # deep dark blue shadow
        self.color_panel   = (5,   15,  35,  200)  # deep blue panel
        self.color_border  = (80,  120, 200, 180)  # blue border
        self.color_title   = (255, 140, 0)      # orange title like best score

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.yes_rect.collidepoint(mouse_pos):
                return 'yes'
            if self.quit_rect.collidepoint(mouse_pos):
                return 'quit'
        return None

    def update(self, mouse_pos, mouse_down):
        self.yes_hovered  = self.yes_rect.collidepoint(mouse_pos)
        self.quit_hovered = self.quit_rect.collidepoint(mouse_pos)

    def draw(self, high_score):
        cx = self.screen_rect.centerx
        cy = self.screen_rect.centery

        # Dark blue overlay matching panel color
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((5, 15, 35, 200))
        self.screen.blit(overlay, (0, 0))

        # Panel behind everything - matching scoreboard panel style
        panel_rect = pygame.Rect(0, 0, 520, 320)
        panel_rect.center = (cx, cy)
        panel_surf = pygame.Surface(
            (panel_rect.width, panel_rect.height), pygame.SRCALPHA
        )
        panel_surf.fill(self.color_panel)
        pygame.draw.rect(
            panel_surf,
            self.color_border,
            panel_surf.get_rect(),
            2,
        )
        self.screen.blit(panel_surf, panel_rect.topleft)

        # GAME OVER title in orange like best score color
        title = self.font_title.render("GAME OVER", True, self.color_title)
        # Shadow first
        title_shadow = self.font_title.render("GAME OVER", True, self.color_shadow)
        self.screen.blit(title_shadow, title_shadow.get_rect(
            center=(cx + 2, cy - 90 + 2))
        )
        self.screen.blit(title, title.get_rect(center=(cx, cy - 90)))

        # Best score in orange matching scoreboard BEST color
        best_label = self.font_sub.render("BEST:", True, self.color_label)
        best_value = self.font_sub.render(str(high_score), True, self.color_high)
        # Shadow
        best_shadow = self.font_sub.render(str(high_score), True, self.color_shadow)
        total_w = best_label.get_width() + 8 + best_value.get_width()
        lx = cx - total_w // 2
        self.screen.blit(best_label, (lx, cy - 20))
        self.screen.blit(best_shadow, (lx + best_label.get_width() + 10, cy - 18))
        self.screen.blit(best_value, (lx + best_label.get_width() + 8, cy - 20))

        # Buttons styled like the panel with blue border
        yes_color  = (10, 40, 90)  if self.yes_hovered  else (5, 25, 60)
        quit_color = (10, 40, 90)  if self.quit_hovered else (5, 25, 60)

        pygame.draw.rect(self.screen, yes_color,
                         self.yes_rect,  border_radius=4)
        pygame.draw.rect(self.screen, quit_color,
                         self.quit_rect, border_radius=4)

        # Button borders in blue matching scoreboard
        pygame.draw.rect(self.screen, (80, 120, 200),
                         self.yes_rect,  2, border_radius=4)
        pygame.draw.rect(self.screen, (80, 120, 200),
                         self.quit_rect, 2, border_radius=4)

        # Button labels in light blue matching scoreboard SCORE color
        yes_col  = self.color_high    if self.yes_hovered  else self.color_current
        quit_col = self.color_high    if self.quit_hovered else self.color_current

        yes_label  = self.font_btn.render("TRY AGAIN", True, yes_col)
        quit_label = self.font_btn.render("QUIT",      True, quit_col)

        # Shadows on button text
        yes_shadow  = self.font_btn.render("TRY AGAIN", True, self.color_shadow)
        quit_shadow = self.font_btn.render("QUIT",      True, self.color_shadow)

        self.screen.blit(yes_shadow, yes_shadow.get_rect(
            center=(self.yes_rect.centerx + 2, self.yes_rect.centery + 2))
        )
        self.screen.blit(quit_shadow, quit_shadow.get_rect(
            center=(self.quit_rect.centerx + 2, self.quit_rect.centery + 2))
        )
        self.screen.blit(yes_label,  yes_label.get_rect(
            center=self.yes_rect.center)
        )
        self.screen.blit(quit_label, quit_label.get_rect(
            center=self.quit_rect.center)
        )


# ──────────────────────────────────────────────────────────────────────────────
# SettingsMenu  –  toggle music & SFX on/off
# ──────────────────────────────────────────────────────────────────────────────

class SettingsMenu:
    """
    A modal-style settings panel with toggle buttons for Music and SFX.

    handle_event() → 'main_menu' | None
    Reads and writes sound_manager.music_on / sfx_on directly.

    Parameters
    ----------
    screen       : pygame.Surface
    sound_manager: SoundManager instance (from sound_manager.py)
    """

    # Colour accents for ON / OFF states
    _C_ON  = C_PIX_GLOW               # green — enabled
    _C_OFF = (180, 60, 60)             # red   — disabled

    def __init__(self, screen, sound_manager):
        self.screen        = screen
        self.sm            = sound_manager
        sw, sh             = screen.get_size()

        self._bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._bg.fill((5, 8, 28, 220))

        self.title_font = _pixel_font(50)
        self.lbl_font   = _pixel_font(40)

        # ── layout ────────────────────────────────────────────────────────
        panel_w, panel_h = 630, 330
        self.panel_rect  = pygame.Rect(
            (sw - panel_w) // 2, (sh - panel_h) // 2, panel_w, panel_h
        )
        px, py = self.panel_rect.x, self.panel_rect.y

        # Toggle buttons — one row each for Music / SFX
        tog_w, tog_h = 150, 50
        row1_y = py + 104
        row2_y = py + 174

        # Music toggle
        self.btn_music = PixelForestButton(
            screen, "MUSIC  ON",
            (px + panel_w - tog_w - 32, row1_y, tog_w, tog_h), 30,
            phase_offset=0.0, accent_color=self._C_ON
        )

        # SFX toggle
        self.btn_sfx = PixelForestButton(
            screen, "SFX  ON",
            (px + panel_w - tog_w - 32, row2_y, tog_w, tog_h), 30,
            phase_offset=1.2, accent_color=self._C_ON
        )

        # Back to main menu
        self.btn_back = PixelForestButton(
            screen, "< MENU",
            (px + 32, py + 305 - 60, 155, 50), 30,
            phase_offset=2.4
        )

        self._buttons = [self.btn_music, self.btn_sfx, self.btn_back]

    # ── helpers ────────────────────────────────────────────────────────────────
    def _refresh_labels(self):
        """Rebuild toggle button text + accent to reflect current on/off state."""
        music_on = self.sm.music_on
        sfx_on   = self.sm.sfx_on

        self.btn_music.text    = "ON"  if music_on else "OFF"
        self.btn_music._accent = self._C_ON   if music_on else self._C_OFF

        self.btn_sfx.text    = "ON"  if sfx_on else "OFF"
        self.btn_sfx._accent = self._C_ON if sfx_on else self._C_OFF

    # ── public API ─────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if self.btn_back.is_clicked(event):
            return 'main_menu'

        if self.btn_music.is_clicked(event):
            self.sm.toggle_music()
            self._refresh_labels()

        if self.btn_sfx.is_clicked(event):
            self.sm.toggle_sfx()
            self._refresh_labels()

        return None

    def update(self, mouse_pos, mouse_down):
        self._refresh_labels()   # keep labels in sync every frame
        for b in self._buttons:
            b.update(mouse_pos, mouse_down)

    def draw(self):
        self.screen.blit(self._bg, (0, 0))

        S  = PIXEL_SIZE
        pr = self.panel_rect

        # Panel background
        pygame.draw.rect(self.screen, C_PIX_DARK, pr)
        pygame.draw.rect(self.screen, C_PIX_MID,  pr.inflate(-S * 4, -S * 4))
        pygame.draw.rect(self.screen, C_PIX_EDGE, pr, width=S * 2)

        # Title
        t_surf = self.title_font.render("SETTINGS", True, C_PIX_GOLD)
        sh_surf = self.title_font.render("SETTINGS", True, (30, 10, 60))
        t_rect  = t_surf.get_rect(centerx=pr.centerx, top=pr.top + 22)
        self.screen.blit(sh_surf, t_rect.move(3, 3))
        self.screen.blit(t_surf,  t_rect)

        # Row labels
        lbl_x = pr.x + 40
        for text, btn in [("Music", self.btn_music), (("Sound Effects"), self.btn_sfx)]:
            lbl  = self.lbl_font.render(text, True, C_PIX_TEXT)
            lbl_rect = lbl.get_rect(
                midleft=(lbl_x, btn.rect.centery + btn._float_offset())
            )
            self.screen.blit(lbl, lbl_rect)

        for b in self._buttons:
            b.draw()