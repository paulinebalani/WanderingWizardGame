import pygame
import os

class Settings:
    def __init__ (self):
        self.screen_width = 1920
        self.screen_height = 1080
        
        bg_title_path = os.path.dirname(__file__)

        bg_title_image = os.path.join(bg_title_path, 'photos', 'last.png')
        forest_image = os.path.join (bg_title_path, 'photos', 'huhu.png')

        self.screen_background = pygame.image.load (bg_title_image)
        self.screen_background = pygame.transform.scale (self.screen_background, (1920, 1080))

        self.screen_background2 = pygame.image.load(forest_image)
        # Keep original size - no scaling/zooming
        img_rect = self.screen_background2.get_rect()
        self.screen_background2 = pygame.transform.scale(
            self.screen_background2, (img_rect.width, self.screen_height))  # only fit height

        self.bg2_x = 0