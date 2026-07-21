import sys
import pygame
import os

from characters import Wizard, GrimReaper
from settings import Settings
from attacks import Attacks
from powers import (
    Dome,
    ThunderStrike,
    wizard_blit_cast_effect, 
    grimreaper_update_flash,
    grimreaper_blit_flash
)
from transition import Transition, Vignette
from lives import Lives
from button import Button, MainMenu, HowToPlay, Credits, QuitConfirm, GameOver, SettingsMenu
from scoreboard import Scoreboard
from sound_manager import SoundManager

# ── Scene constants ────────────────────────────────────────────────────────
SCENE_MAIN_MENU   = "main_menu"
SCENE_HOW_TO_PLAY = "how_to_play"
SCENE_CREDITS     = "credits"
SCENE_QUIT_CONFIRM= "quit_confirm"
SCENE_SETTINGS    = "settings"
SCENE_GAME        = "game"


class WanderingWizard:

    def __init__(self):
        pygame.init()

        self.settings = Settings()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width  = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        self.clock = pygame.time.Clock()
        pygame.display.set_caption('Wandering Wizard')

        icon_path = os.path.dirname(__file__)
        icon_image = os.path.join(icon_path, 'photos', 'wiz_front(1).png')
        icon_surface = pygame.image.load(icon_image)
        pygame.display.set_icon(icon_surface)

        # ── Game objects ────────────────────────────────────────────────
        self.wizard       = Wizard(self)
        self.dome         = Dome(self)
        self.gr           = GrimReaper(self)
        self.attack       = Attacks(self)
        self.transition   = Transition(self)
        self.lives        = Lives(self)
        self.vignette     = Vignette(self)
        self.scoreboard = Scoreboard(self.screen)
        self.game_over_screen = GameOver(self.screen)
        self.game_over_active = False

        # ── Game-state flags ────────────────────────────────────────────
        self.game_active      = False
        self.play_button      = Button(self, "Play")   # kept but unused in new flow

        self.show_wizard      = False
        self.show_grimreaper  = False
        GrimReaper.spawn_timer = 0

        self.show_text        = False
        self.sliding_out      = False

        self.thunder_strikes  = []
        self.last_strike_time = 0
        self.strike_cooldown  = 10000
        self.strike_ever_used = False

        """VIGNETTE SETUP"""
        self.vignette_surf    = None
        self.vignette_alpha   = 0
        self.enemies_killed   = 0
        self.vignette.build_vignette()

        GrimReaper.all_enemies  = []
        GrimReaper.spawn_timer  = 0

        # ── Scene / UI objects ──────────────────────────────────────────
        self.scene       = SCENE_MAIN_MENU
        self.main_menu   = MainMenu(self.screen)
        self.how_to_play = HowToPlay(self.screen)
        self.credits     = Credits(self.screen)
        self.quit_confirm= QuitConfirm(self.screen)

        # ── Sound ────────────────────────────────────────────────────────
        self.sounds = SoundManager()
        self.sounds.play_music()
        self.settings_menu = SettingsMenu(self.screen, self.sounds)

    # ════════════════════════════════════════════════════════════════════════
    # Scene switching helper
    # ════════════════════════════════════════════════════════════════════════
    def _switch_scene(self, new_scene):
        if new_scene == SCENE_HOW_TO_PLAY:
            self.how_to_play = HowToPlay(self.screen)   # reset pages
        if new_scene == SCENE_CREDITS:
            self.credits = Credits(self.screen)          # reset scroll
        if new_scene == SCENE_SETTINGS:
            self.settings_menu = SettingsMenu(self.screen, self.sounds)
        self.scene = new_scene

    # ════════════════════════════════════════════════════════════════════════
    # Start the actual game (called when Start is confirmed)
    # ════════════════════════════════════════════════════════════════════════
    def _start_game(self):
        self.scene       = SCENE_GAME
        self.game_active = True
        self.scoreboard.reset_score()
        self.transition.pixelate_transition(
            self.settings.screen_background,
            self.settings.screen_background2)
        self.transition.first_bg       = self.settings.screen_background2
        self.transition.on_first_bg    = False
        pygame.mouse.set_visible(False)

    # ════════════════════════════════════════════════════════════════════════
    # Event handling
    # ════════════════════════════════════════════════════════════════════════
    def check_events(self):
        mouse_pos  = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.scoreboard.reset_high_score() 
                sys.exit()

            # ── ESC: always go back to main menu (or quit from menu) ────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.scene == SCENE_MAIN_MENU:
                        self._switch_scene(SCENE_QUIT_CONFIRM)
                    elif self.scene == SCENE_GAME:
                        pass   # keep playing; remove if you want ESC to quit
                    else:
                        self._switch_scene(SCENE_MAIN_MENU)
                        pygame.mouse.set_visible(True)

            # ── Route events to the active scene ────────────────────────
            if self.scene == SCENE_MAIN_MENU:
                action = self.main_menu.handle_event(event)
                if action == 'start':
                    self._start_game()
                elif action == 'how_to_play':
                    self._switch_scene(SCENE_HOW_TO_PLAY)
                elif action == 'credits':
                    self._switch_scene(SCENE_CREDITS)
                elif action == 'quit_confirm':
                    self._switch_scene(SCENE_QUIT_CONFIRM)
                elif action == 'settings':
                    self._switch_scene(SCENE_SETTINGS)

            elif self.scene == SCENE_HOW_TO_PLAY:
                result = self.how_to_play.handle_event(event)
                if result == 'main_menu':
                    self._switch_scene(SCENE_MAIN_MENU)
                    pygame.mouse.set_visible(True)

            elif self.scene == SCENE_CREDITS:
                result = self.credits.handle_event(event)
                if result == 'main_menu':
                    self._switch_scene(SCENE_MAIN_MENU)
                    pygame.mouse.set_visible(True)

            elif self.scene == SCENE_QUIT_CONFIRM:
                result = self.quit_confirm.handle_event(event)
                if result == 'yes':
                    self.scoreboard.reset_high_score() 
                    pygame.quit()
                    sys.exit()
                elif result == 'no':
                    self._switch_scene(SCENE_MAIN_MENU)

            elif self.scene == SCENE_SETTINGS:
                result = self.settings_menu.handle_event(event)
                if result == 'main_menu':
                    self._switch_scene(SCENE_MAIN_MENU)
                    pygame.mouse.set_visible(True)

            elif self.scene == SCENE_GAME:
                #self._handle_game_event(event)
                if self.game_over_active:
                    result = self.game_over_screen.handle_event(
                        event, pygame.mouse.get_pos()
                    )
                    if result == 'yes':
                        self.game_over_active = False
                        self._restart_game()        # see below
                    elif result == 'quit':
                        self.scoreboard.reset_high_score()
                        pygame.quit()
                        sys.exit()
                else:
                    self._handle_game_event(event)

        # ── Per-frame update for scene UI ────────────────────────────────
        if self.scene == SCENE_MAIN_MENU:
            self.main_menu.update(mouse_pos, mouse_down)
        elif self.scene == SCENE_HOW_TO_PLAY:
            self.how_to_play.update(mouse_pos, mouse_down)
        elif self.scene == SCENE_CREDITS:
            self.credits.update(mouse_pos, mouse_down)
        elif self.scene == SCENE_QUIT_CONFIRM:
            self.quit_confirm.update(mouse_pos, mouse_down)
        elif self.scene == SCENE_SETTINGS:
            self.settings_menu.update(mouse_pos, mouse_down)
        elif self.scene == SCENE_GAME:
            self._update_game(mouse_pos)

    def _handle_game_event(self, event):
        """Handle keyboard/mouse events while the game is running."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.scoreboard.reset_high_score() 
                sys.exit()

            """FOR TRANSITION"""
            if event.key == pygame.K_RETURN:
                if self.transition.on_first_bg:
                    self.transition.pixelate_transition(
                        self.settings.screen_background,
                        self.settings.screen_background2)
                    self.transition.first_bg       = self.settings.screen_background2
                    self.transition.on_first_bg    = False

    def _update_game(self, mouse_pos):
        """Per-frame gameplay input (movement, powers)."""
        
        # --- FREEZE everything when game over ---
        if self.game_over_active:
            return  # stop all updates immediately
        
        speed = 5
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.wizard.moving_left  = True
            self.wizard.moving_right = False
            self.settings.bg2_x += speed
        elif keys[pygame.K_RIGHT]:
            self.wizard.moving_right = True
            self.wizard.moving_left  = False
            self.settings.bg2_x -= speed
        else:
            self.wizard.moving_left  = False
            self.wizard.moving_right = False

        self.wizard.update(self.dt)

        # --- Loop the background ---
        # --- Smooth seamless background loop ---
        img_width = self.settings.screen_background2.get_width()
        self.settings.bg2_x = self.settings.bg2_x % img_width

        # --- Dome power (K_d) ---
        if keys[pygame.K_d]:
            current_time = pygame.time.get_ticks()
            if not self.dome.on_cooldown and not self.dome.dome_active:
                self.dome.dome_active     = True
                self.dome.glowing         = True
                self.dome.dome_start_time = current_time

        # --- Thunder Strike (K_a) ---
        if keys[pygame.K_a]:
            current_time    = pygame.time.get_ticks()
            time_since_last = current_time - self.last_strike_time
            if time_since_last >= self.strike_cooldown:
                strike = ThunderStrike(self)
                self.thunder_strikes.append(strike)
                self.last_strike_time = current_time
                self.strike_ever_used = True
                # Play thunder SFX the instant the strike is cast
                self.sounds.play_sfx('lightning_kill')

        # --- Keep player on screen (all 4 edges) ---
        self.wizard.rect.x = max(
            0, min(self.wizard.rect.x, self.settings.screen_width - self.wizard.rect.width))
        self.wizard.rect.y = max(
            0, min(self.wizard.rect.y, self.settings.screen_height - self.wizard.rect.height))
        
    def _restart_game(self):
        """Reset everything for a fresh game, keeping high score."""
        self.enemies_killed       = 0
        self.lives.current_lives  = self.lives.max_lives
        self.lives.last_hit_time  = 0
        GrimReaper.all_enemies    = []
        GrimReaper.spawn_timer    = 0
        GrimReaper.speed          = 3        # reset speed
        self.thunder_strikes      = []
        self.strike_ever_used     = False
        self.dome.dome_active     = False
        self.dome.on_cooldown     = False
        self.scoreboard.reset_score()
        self.sounds.reset_game_over_flag()   # allow game-over jingle to fire again
        self.wizard.rect = self.wizard.wizard_image.get_rect(midbottom = (self.settings.screen_width // 2, 
                                                            self.settings.screen_height - 150))
        self.wizard.frame_index  = 0
        self.wizard.anim_timer   = 0.0
        self.wizard.is_moving    = False

        pygame.mouse.set_visible(False)

    # ════════════════════════════════════════════════════════════════════════
    # Rendering
    # ════════════════════════════════════════════════════════════════════════
    def update_screen(self):
        if self.scene == SCENE_MAIN_MENU:
            # Draw the game background first, then overlay the menu
            self.screen.blit(self.settings.screen_background, (0, 0))
            self.main_menu.draw()

        elif self.scene == SCENE_HOW_TO_PLAY:
            self.screen.blit(self.settings.screen_background, (0, 0))
            self.how_to_play.draw()

        elif self.scene == SCENE_CREDITS:
            self.screen.blit(self.settings.screen_background, (0, 0))
            self.credits.draw()

        elif self.scene == SCENE_QUIT_CONFIRM:
            self.screen.blit(self.settings.screen_background, (0, 0))
            if not self.game_active:
                self.main_menu.draw()
            self.quit_confirm.draw()

        elif self.scene == SCENE_SETTINGS:
            self.screen.blit(self.settings.screen_background, (0, 0))
            self.main_menu.draw()
            self.settings_menu.draw()

        elif self.scene == SCENE_GAME:
            self._draw_game()

        pygame.display.flip()

    def _draw_game(self):
        """All game-play rendering."""

        # --- Draw first background (stays fixed) ---
        self.screen.blit(self.transition.first_bg, (0, 0))

        # --- Draw second background (smooth seamless loop) ---
        img_width = self.settings.screen_background2.get_width()
        x = -((-self.settings.bg2_x) % img_width)

        copies = (self.settings.screen_width // img_width) + 2
        for i in range(copies):
            self.screen.blit(
                self.settings.screen_background2,
                (x + i * img_width, 0)
            )

        # --- Dome glow ---
        self.dome.player_glow(self.wizard.rect.midbottom)

        self.show_wizard = True
        self.show_grimreaper = True

        # =========================================================
        # THUNDER STRIKES
        # =========================================================
        for strike in self.thunder_strikes[:]:
            strike.update()
            strike.draw()

            if strike.is_expired() or strike.is_off_screen():
                strike.expire()
                self.thunder_strikes.remove(strike)

        # =========================================================
        # GRIM REAPER UPDATE (movement + spawn)
        # =========================================================
        if not self.game_over_active and self.show_grimreaper:
            _before = len(GrimReaper.all_enemies)
            GrimReaper.update_all(
                dome_pos=self.wizard.rect.center,
                dome_radius=self.dome.current_radius,
                dome_active=self.dome.dome_active,
                show_grimreaper=self.show_grimreaper,
                dt=self.dt
            )
            # Each enemy removed by the dome → play dome kill SFX
            _killed_by_dome = _before - len(GrimReaper.all_enemies)
            for _ in range(_killed_by_dome):
                self.sounds.play_sfx('dome_kill')

        else:
            # freeze enemies on game over
            for grim in GrimReaper.all_enemies:
                grim.blit_enemy()

        # =========================================================
        # PLAYER COLLISION (LIVES SYSTEM)
        # =========================================================
        if not self.game_over_active:
            current_time = pygame.time.get_ticks()

            # Shrink the rects used for collision so the wizard only
            # takes damage when the sprites are actually touching
            # (the source images have a lot of transparent padding).
            wizard_hitbox = self.wizard.rect.inflate(-110, -110)

            for grim in GrimReaper.all_enemies[:]:
                grim_hitbox = grim.rect.inflate(-110, -110)
                if grim_hitbox.colliderect(wizard_hitbox):
                    if current_time - self.lives.last_hit_time > self.lives.hit_cooldown:
                        self.lives.current_lives -= 1
                        self.lives.last_hit_time = current_time
                        GrimReaper.all_enemies.remove(grim)
                        # Only play the death voice if the wizard survives the hit
                        if self.lives.current_lives > 0:
                            self.sounds.play_sfx('wizard_death')

            if self.lives.current_lives <= 0:
                self.game_over_active = True
                # Final death → game-over jingle only (no wizard_death SFX)
                self.sounds.trigger_game_over_sound()

        # =========================================================
        # GRIM REAPER FLASH SYSTEM (ONLY PLACE THAT HANDLES DEATH)
        # =========================================================
        for enemy in GrimReaper.all_enemies[:]:

            # update flash state
            done = grimreaper_update_flash(enemy)

            # draw flash effect
            grimreaper_blit_flash(enemy)

            # remove ONLY when flash fully completes
            if done:
                if enemy in GrimReaper.all_enemies:
                    GrimReaper.all_enemies.remove(enemy)

                    self.enemies_killed += 1

                    if self.enemies_killed % 5 == 0:
                        GrimReaper.increase_speed()

        # =========================================================
        # DRAW WIZARD
        # =========================================================
        if self.show_wizard:
            self.wizard.blit_wizard()
            wizard_blit_cast_effect(self.wizard)

        # =========================================================
        # VIGNETTE EFFECT
        # =========================================================
        if self.enemies_killed >= 20:
            self.vignette_alpha = min(self.vignette_alpha + 4, 255)

            if self.vignette.vignette_surf:
                self.vignette.vignette_surf.set_alpha(self.vignette_alpha)
                self.screen.blit(self.vignette.vignette_surf, (0, 0))

        # =========================================================
        # HUD
        # =========================================================
        self.attack.dome_cooldown()
        self.attack.strike_cooldown()
        self.lives.blit_lives()
        self.scoreboard.update_score(self.enemies_killed)
        self.scoreboard.draw()
        self.scoreboard.draw_level_progress(self.enemies_killed, kills_needed=20)

        # =========================================================
        # GAME OVER OVERLAY
        # =========================================================
        if self.game_over_active:
            overlay = pygame.Surface(
                (self.settings.screen_width, self.settings.screen_height),
                pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

            self.game_over_screen.update(
                pygame.mouse.get_pos(),
                pygame.mouse.get_pressed()[0]
            )
            self.game_over_screen.draw(self.scoreboard.high_score)
            pygame.mouse.set_visible(True)
    # ════════════════════════════════════════════════════════════════════════
    # Main loop
    # ════════════════════════════════════════════════════════════════════════
    def run_game(self):
        try:
            while True:
                self.dt = self.clock.tick(60) / 1000
                self.check_events()
                self.update_screen()
        finally:
            # Reset high score when player fully exits the game
            self.scoreboard.reset_high_score()


if __name__ == '__main__':
    ww = WanderingWizard()
    ww.run_game()