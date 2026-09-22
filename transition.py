import pygame   #pygame library
import sys      #to allow clean program exit
import math

from settings import Settings

class Transition:
    def __init__ (self, game):
        self.game = game            # needed so the transition can present
                                     # each frame through the same real-screen
                                     # scaling as the rest of the game
        self.screen = game.screen
        self.settings = game.settings
        self.clock = pygame.time.Clock()    #to control the frame rate

        """BACKGROUND TRANSITION"""
        self.first_bg = self.settings.screen_background
        self.second_bg = self.settings.screen_background2
        self.on_first_bg = True             # used to track which bachground is currently active

    def ease_out_cubic(self, p):            # 'p' is a progress value from 0.0 to 1.0
        # Easing function = used to slow down the animation near the end for a smoother transition
        return 1 - (1 - p) ** 3             # returns a value that starts fast and slowwing down toward 1.0
    
    def pixelate_transition (self, old_image, new_image, duration = 120): # duration = the total number of frames the transition lasts (default: 120 frames = 2 secs at 60fps)
        w, h = self.screen.get_size()   # to get the width and height of the screen

        old = old_image.convert()       # convert old image to an optimized pixel format for faster blitting/copying a block of pixels from one place to another
        new = new_image.convert()

        for frame in range(duration):
            for event in pygame.event.get():    # process all pending events to keep window responsive
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            p = frame / duration

            if p < 0.5:     #first half of the transition: pixelate the old image (blocks grow larger = more pixelated)
                progress = p / 0.5
                block_size = max(1, int(1 + progress * 80))
                source = old
            else:           # second half of the transition: de-pixelate the new image (blocks shrink = clearer)
                progress = (p - 0.5) / 0.5
                block_size = max(1, int(80 - progress * 79))
                source = new

            """SCALE THE SOURCE IMAGE DOWN TO A TINY RESOLUTION (CREATES  THE CHUNKY PIXEL LOOK)"""
            small = pygame.transform.scale(source, (w // block_size, h // block_size))

            """SCALE THE TINY IMAGE BACK UP TO FULL SCREEN SIZE"""
            pixelated = pygame.transform.scale(small, (w, h))

            self.screen.blit(pixelated, (0,0))      # draw the image in the screen
            self.game.present_frame()               # scale + display it on the real screen
            self.clock.tick(60)                     # limit the loop to 60 frames per second

class Vignette (Transition):
    def __init__ (self, games):
        self.screen = games.screen
        self.settings = games.settings
        
    def build_vignette (self):
        width = self.settings.screen_width
        height = self.settings.screen_height
        self.vignette_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.vignette_surf.fill((0, 0, 0, 0))

        #border = min(width, height // 3)
        border = 1000

        for x in range(width):
            for y in range(height):
                #Distance from nearest edge
                dist_left = x
                dist_right = width - x
                dist_top = y
                #dist_bottom = height - y

                nearest = min(dist_left, dist_right, dist_top)

                if nearest < border:
                    alpha = int((1 - nearest / border) ** 2 * 255)
                    self.vignette_surf.set_at((x, y), (0, 0, 0, alpha))