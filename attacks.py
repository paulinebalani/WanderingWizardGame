import pygame
import math 

from powers import Dome, ThunderStrike

class Attacks:
    def __init__ (self, games):
        self.games = games
        self.dome = games.dome

    def dome_cooldown (self):
        if not self.dome.on_cooldown:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.dome.cooldown_start
        remaining = self.dome.cooldown- elapsed

        progress = remaining / self.dome.cooldown

        """circle settings"""
        center = (80, 80)   #top left position
        radius = 50         #size of circle
        thickness = 8       #thickness of ring

        pygame.draw.circle(self.games.screen, 
                           (255, 255, 0), #color of the circle
                           center, radius, thickness)
        
        #draws the progress of the cooldown
        start_angle = -math.pi / 2      #start from top
        end_angle = start_angle + (2 * math.pi * progress)      #shrinks while cooling down

        steps = 100     #smoothness of arc

        points = []
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * i / steps
            circle_x = center[0] + int(radius * math.cos(angle))
            circle_y = center[1] + int(radius * math.sin(angle))
            points.append((circle_x, circle_y))

        #draw arc as connected lines
        if len(points) > 1:
            pygame.draw.lines (self.games.screen, 
                               (255, 234, 0),   #color of the progress
                               False, points, thickness)
            
        #draw dome icon in center
        pygame.draw.circle (self.games.screen, 
                            (255, 234, 0),
                            center, radius - 15, 3)
        
        seconds_left = math.ceil(remaining / 1000)

        #Only show cooldown if it is still counting down
        if seconds_left > 0:
            font = pygame.font.SysFont('Arial', 22, bold = True)
            text = font.render(str(seconds_left), True, (255, 255, 0))
            text_rect = text.get_rect (center = center)
            self.games.screen.blit(text, text_rect)

    def strike_cooldown(self):
        #DON'T SHOW IF STRIKE WAS NEVER USED
        if not self.games.strike_ever_used:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.games.last_strike_time
        remaining = self.games.strike_cooldown - elapsed

        if remaining <= 0:
            return
        
        progress = remaining / self.games.strike_cooldown

        """circle settings"""
        center = (80, 200)   #below the strike cooldown
        radius = 50         #size of circle
        thickness = 8       #thickness of ring

        """Background circle"""
        pygame.draw.circle(self.games.screen, 
                           (0, 150, 255), #color of the circle
                           center, radius, thickness)
        
        """draws the progress of the cooldown/ starts full, shrinks as cooldown runs out"""
        start_angle = -math.pi / 2      #start from top
        end_angle = start_angle + (2 * math.pi * progress)      #shrinks while cooling down

        steps = 100     #smoothness of arc

        points = []
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * i / steps
            circle_x = center[0] + int(radius * math.cos(angle))
            circle_y = center[1] + int(radius * math.sin(angle))
            points.append((circle_x, circle_y))

        #draw arc as connected lines
        if len(points) > 1:
            pygame.draw.lines (self.games.screen, 
                               (0, 150, 255),   #color of the progress
                               False, points, thickness)
            
        #draw dome icon in center
        pygame.draw.circle (self.games.screen, 
                            (0, 150, 255),
                            center, radius - 15, 3)
        
        seconds_left = math.ceil(remaining / 1000)

        #Only show cooldown if it is still counting down
        if seconds_left > 0:
            font = pygame.font.SysFont('Arial', 22, bold = True)
            text = font.render(str(seconds_left), True, (0, 150, 255))
            text_rect = text.get_rect (center = center)
            self.games.screen.blit(text, text_rect)