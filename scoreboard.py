import pygame
import os
import json

SCORE_FILE = os.path.join(os.path.dirname(__file__), "highscore.json")


def _load_high_score():
    """Load the high score from file."""
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except (json.JSONDecodeError, IOError):
            return 0
    return 0


def _save_high_score(score):
    """Save the high score to file."""
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump({"high_score": score}, f)
    except IOError:
        pass


class Scoreboard:
    # Pixel font digit segments (5x7 bitmap for 0-9)
    DIGITS = {
        '0': [
            "01110",
            "10001",
            "10011",
            "10101",
            "11001",
            "10001",
            "01110",
        ],
        '1': [
            "00100",
            "01100",
            "00100",
            "00100",
            "00100",
            "00100",
            "01110",
        ],
        '2': [
            "01110",
            "10001",
            "00001",
            "00110",
            "01000",
            "10000",
            "11111",
        ],
        '3': [
            "11111",
            "00010",
            "00100",
            "00110",
            "00001",
            "10001",
            "01110",
        ],
        '4': [
            "00010",
            "00110",
            "01010",
            "10010",
            "11111",
            "00010",
            "00010",
        ],
        '5': [
            "11111",
            "10000",
            "11110",
            "00001",
            "00001",
            "10001",
            "01110",
        ],
        '6': [
            "00110",
            "01000",
            "10000",
            "11110",
            "10001",
            "10001",
            "01110",
        ],
        '7': [
            "11111",
            "00001",
            "00010",
            "00100",
            "01000",
            "01000",
            "01000",
        ],
        '8': [
            "01110",
            "10001",
            "10001",
            "01110",
            "10001",
            "10001",
            "01110",
        ],
        '9': [
            "01110",
            "10001",
            "10001",
            "01111",
            "00001",
            "00010",
            "01100",
        ],
    }

    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()

        self.current_score = 0
        self.high_score = _load_high_score()

        # Pixel size for each "dot" in the bitmap font
        self.pixel_size = 6
        # Gap between digits
        self.digit_gap = 4
        # Digit dimensions based on bitmap (5 wide, 7 tall)
        self.digit_w = 5 * self.pixel_size
        self.digit_h = 7 * self.pixel_size

        # Colors
        self.color_high    = (255, 140, 0)    # orange for best - matches the lantern
        self.color_current = (180, 210, 255)  # light blue for score - matches background
        self.color_label   = (120, 150, 200)  # muted blue for labels
        self.color_shadow  = (10,  20,  40)   # deep dark blue shadow

        # Label font (small system font used only for "BEST" / "SCORE" text)
        self.label_font = pygame.font.SysFont("couriernew", 15, bold=True)
        if self.label_font is None:
            self.label_font = pygame.font.SysFont(None, 14)

        # Padding from top of screen
        self.top_padding = 10

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_score(self, kills):
        """Call this whenever enemies_killed changes."""
        self.current_score = kills
        if self.current_score > self.high_score:
            self.high_score = self.current_score
            _save_high_score(self.high_score)

    def reset_score(self):
        """Reset current score (call on new game). High score persists."""
        self.current_score = 0

    def reset_high_score(self):
        """Delete the saved high score file."""
        if os.path.exists(SCORE_FILE):
            os.remove(SCORE_FILE)
        self.high_score = 0

    def draw(self):
        """Draw the scoreboard at the upper-center of the screen."""
        # Render both rows and measure total width so we can center them
        hs_surface = self._render_score_row(
            "BEST", self.high_score, self.color_high
        )
        cs_surface = self._render_score_row(
            "SCORE", self.current_score, self.color_current
        )

        max_w = max(hs_surface.get_width(), cs_surface.get_width())
        cx = self.screen_rect.centerx

        row_spacing = 6
        total_h = hs_surface.get_height() + row_spacing + cs_surface.get_height()

        # Subtle dark backing panel
        panel_pad_x = 14
        panel_pad_y = 8
        panel_rect = pygame.Rect(
            cx - max_w // 2 - panel_pad_x,
            self.top_padding - panel_pad_y,
            max_w + panel_pad_x * 2,
            total_h + panel_pad_y * 2,
        )
        panel_surf = pygame.Surface(
            (panel_rect.width, panel_rect.height), pygame.SRCALPHA
        )
        panel_surf.fill((5, 15, 35, 180))    # deep blue instead of black
        # and the border:
        pygame.draw.rect(
            panel_surf,
            (80, 120, 200, 180),   # blue border instead of gold
            panel_surf.get_rect(),
            2,
        )
        self.screen.blit(panel_surf, panel_rect.topleft)

        # Blit high score row (centered)
        hs_x = cx - hs_surface.get_width() // 2
        hs_y = self.top_padding
        self.screen.blit(hs_surface, (hs_x, hs_y))

        # Blit current score row (centered)
        cs_x = cx - cs_surface.get_width() // 2
        cs_y = hs_y + hs_surface.get_height() + row_spacing
        self.screen.blit(cs_surface, (cs_x, cs_y))

        # Remember bottom of panel so the level-progress line can be
        # drawn just beneath it.
        self.panel_bottom = panel_rect.bottom

    def draw_level_progress(self, kills, kills_needed=20):
        """Draw a small line under the scoreboard panel indicating how
        many more Grim Reaper kills are needed before Level 2
        (the vignette effect) appears."""
        cx = self.screen_rect.centerx
        y  = getattr(self, "panel_bottom", self.top_padding) + 6

        if kills >= kills_needed:
            text = "SIGHT DECREASED"
            color = (255, 140, 0)
        else:
            remaining = kills_needed - kills
            text = f"DECREASING SIGHT IN {remaining} KILL{'S' if remaining != 1 else ''}"
            color = self.color_label

        level_font = pygame.font.SysFont("couriernew", 13, bold=True)
        level_surf = level_font.render(text, True, color)

        # Small backing so it's readable over the background
        pad_x, pad_y = 8, 4
        bg_rect = pygame.Rect(
            cx - level_surf.get_width() // 2 - pad_x,
            y - pad_y,
            level_surf.get_width() + pad_x * 2,
            level_surf.get_height() + pad_y * 2,
        )
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((5, 15, 35, 160))
        pygame.draw.rect(bg_surf, (80, 120, 200, 160), bg_surf.get_rect(), 1)
        self.screen.blit(bg_surf, bg_rect.topleft)

        self.screen.blit(level_surf, (cx - level_surf.get_width() // 2, y))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _render_score_row(self, label, value, number_color):
        """Return a Surface with 'LABEL  [pixel digits]' side by side."""
        label_surf = self.label_font.render(label + ":", True, self.color_label)
        digits_surf = self._render_number(str(value), number_color)

        gap = 8
        total_w = label_surf.get_width() + gap + digits_surf.get_width()
        total_h = max(label_surf.get_height(), digits_surf.get_height())

        row = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        # Vertically center each part
        label_y = (total_h - label_surf.get_height()) // 2
        digits_y = (total_h - digits_surf.get_height()) // 2
        row.blit(label_surf, (0, label_y))
        row.blit(digits_surf, (label_surf.get_width() + gap, digits_y))
        return row

    def _render_number(self, text, color):
        """Render a string of digits using the bitmap pixel font."""
        ps = self.pixel_size
        dw = self.digit_w
        dh = self.digit_h
        gap = self.digit_gap

        total_w = len(text) * (dw + gap) - gap
        surf = pygame.Surface((total_w, dh), pygame.SRCALPHA)

        shadow_offset = 2
        shadow_color = self.color_shadow

        for i, ch in enumerate(text):
            bitmap = self.DIGITS.get(ch)
            if bitmap is None:
                continue
            ox = i * (dw + gap)
            for row_idx, row in enumerate(bitmap):
                for col_idx, bit in enumerate(row):
                    if bit == '1':
                        rx = ox + col_idx * ps
                        ry = row_idx * ps
                        # Shadow
                        pygame.draw.rect(
                            surf, shadow_color,
                            (rx + shadow_offset, ry + shadow_offset, ps, ps)
                        )
                        # Main pixel
                        pygame.draw.rect(
                            surf, color,
                            (rx, ry, ps, ps)
                        )
        return surf