#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
import pygame


class GcodeGuiPygame(object):
    """Pygame based user Interface"""

    def __init__(self, automatic):
        self.automatic = automatic
        # initialize
        pygame.init()
        self.font = pygame.font.Font(None, 36)
        self.background = pygame.display.set_mode((800, 600))
        self.text_surface = self.background.subsurface((5, 5, 278, 590))
        self.surface = self.background.subsurface((283, 5, 512, 512))
        self.surface.fill((0, 0, 0))
        pygame.display.flip()
        self.draw_grid()
        # initialize some variables
        self.controller = None
        self.parser = None

    def draw_grid(self):
        """
        draw grid on pygame window
        first determine, which axis are to draw
        second determine what the min_position and max_positions of each motor are

        surface.X : self.motors["X"].min_position <-> surface.get_width() = self.motors["X"].max_position
        surface.Y : self.motors["Y"].min_position <-> surface.get_height() = self.motors["Y"].max_position
        """
        color = pygame.Color(0, 50, 0, 255)
        for x in range(0, self.surface.get_height(), 10):
            pygame.draw.line(self.surface, color, (x, 0), (x, self.surface.get_height()), 1)
        for y in range(0, self.surface.get_width(), 10):
            pygame.draw.line(self.surface, color, (0, y), (self.surface.get_width(), y), 1)
        color = pygame.Color(0, 100, 0, 255)
        pygame.draw.line(self.surface, color, (self.surface.get_width() / 2, 0), (self.surface.get_width() / 2, self.surface.get_height()))
        pygame.draw.line(self.surface, color, (0, self.surface.get_height() / 2), (self.surface.get_width(), self.surface.get_height() / 2))
        # draw motor scales
        color = pygame.Color(100, 0, 0, 255)
        pygame.draw.line(self.surface, color, (self.surface.get_width() - 10, 0), (self.surface.get_width() - 10, self.surface.get_height()))
        pygame.draw.line(self.surface, color, (0, self.surface.get_height() - 10), (self.surface.get_width(), self.surface.get_height() - 10))

    def set_controller(self, controller):
        self.controller = controller

    def controller_cb(self, *args):
        """called from controller to inform about changes"""
        newposition = args[0]
        start = (self.controller.resolution * self.controller.position.X, self.controller.resolution * self.controller.position.Y)
        stop = (self.controller.resolution * newposition.X, self.controller.resolution * newposition.Y)
        pygame.draw.line(self.surface, self.controller.pygame_color, start, stop, 1)
        # set red dot at motor position
        self.surface.set_at((self.controller.motors["X"].position, self.controller.motors["Y"].position), pygame.Color(255, 0, 0, 255))
        # display motor positions
        text = self.font.render("%s" % self.controller.motors["X"].position, 1, (255, 255, 255, 255))
        textpos = text.get_rect()
        self.text_surface.blit(text, textpos)
        self.update()

    def set_parser(self, parser):
        self.parser = parser

    def parser_cb(self, *args):
        """called from parser to inform about changes"""
        self.update()

    def update(self):
        self.text_surface.fill((0,0,0,0))
        text = self.font.render("%s" % self.controller.stats.max_x, 1, (255, 255, 255, 255))
        textpos = text.get_rect()
        self.text_surface.blit(text, textpos)
        pygame.display.flip()
        # automatic stepping or keypress
        if self.automatic is False:
            while (pygame.event.wait().type != pygame.KEYDOWN):
                pass
