import pygame
import os

from settings import Settings

class Lives:
    def __init__ (self, laro):
        self.screen = laro.screen
        self.settings = laro.settings
        self.screen_rect = laro.screen.get_rect()

        heart_path = os.path.dirname(__file__)

        screen_heart = os.path.join(heart_path, 'photos', 'heart.png')

        self.heart_image = pygame.image.load(screen_heart)
        self.heart_image = pygame.transform.scale(self.heart_image, (90, 90))

        self.max_lives = 3
        self.current_lives = 3      #tracking the lives

        self.hit_cooldown = 1500    #1.5 secs before the wizard can be hit again
        self.last_hit_time = 0      #track last hit time

    def blit_lives(self):
        """DRAW THE HEARTS IN THE UPPER RIGHT OF THE SCREEN"""
        positions = [
            (self.screen_rect.right - 120, 30),   #nasa pinakaright
            (self.screen_rect.right - 210, 30),  #gitna
            (self.screen_rect.right - 300, 30),  #pinakaleft
        ]

        for i in range(self.current_lives):
            self.screen.blit(self.heart_image, positions[i])