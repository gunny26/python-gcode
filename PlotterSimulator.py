#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
import pygame
import time


class PlotterSimulator(object):
    """Pygame Simulation of Plotter"""

    def __init__(self, automatic):
        self.automatic = automatic
        # initialize pygame
        pygame.init()
        self.font = pygame.font.Font(None, 28)
        self.background = pygame.display.set_mode((800, 600))
        self.text_surface = self.background.subsurface((5, 5, 278, 590))
        # drawing subsurface, where plot and grid will be shown
        self.draw_surface = self.background.subsurface((283, 5, 512, 512))
        self.grid_surface = pygame.Surface((500, 400))
        self.grid_surface.set_colorkey((0, 0, 0))
        self.grid_surface.fill((0, 0, 0))
        self.draw_surface.blit(self.grid_surface, (0, 0))
        self.plot_surface = pygame.Surface((500, 400))
        self.plot_surface.set_colorkey((0, 0, 0))
        self.plot_surface.fill((0, 0, 0))
        self.draw_surface.blit(self.plot_surface, (0, 0))
        self.pen_surface = pygame.Surface((500, 400))
        self.pen_surface.set_colorkey((0, 0, 0))
        self.pen_surface.fill((0, 0, 0))
        self.draw_surface.blit(self.pen_surface, (0, 0))
        pygame.display.flip()
        self.draw_grid()
        # initialize some variables
        self.controller = None
        self.pen_color = (0, 0, 0)
        self.step_counter = 0
        self.parser = None
        self.command_counter = 0
        self.start_time = time.time()

    def set_controller(self, controller):
        """called to set controller object"""
        self.controller = controller
        self.width = controller.transformer.width
        self.height = controller.transformer.width
        self.scale = controller.transformer.scale
        self.draw_scale = self.scale * self.draw_surface.get_width() / self.width
        self.old_position = (controller.position.X, controller.position.Y)
        self.new_position = (controller.position.X, controller.position.Y)

    def controller_cb(self, *args):
        """called from controller to inform about changes"""
        self.old_position = self.new_position
        self.step_counter += 1
        # set pen color according to z position,
        # z below zero indicates drawing
        self.pen_color = (32, 32, 32)
        if self.controller.position.Z < 0.0 :
            self.pen_color = (0, 255, 0)
        self.new_position = (self.controller.position.X * self.draw_scale, self.controller.position.Y * self.draw_scale)
        self.update()

    def set_parser(self, parser):
        """called to set parser object"""
        self.parser = parser

    def parser_cb(self, *args):
        """called from parser to inform about changes"""
        self.command_counter += 1
        self.update()

    def draw_grid(self):
        """
        draw grid on pygame window
        first determine, which axis are to draw
        second determine what the min_position and max_positions of each motor are

        surface.X : self.motors["X"].min_position <-> surface.get_width() = self.motors["X"].max_position
        surface.Y : self.motors["Y"].min_position <-> surface.get_height() = self.motors["Y"].max_position
        """
        self.plot_surface.fill((0, 0, 0))
        width = self.grid_surface.get_width()
        height = self.grid_surface.get_height()
        color = pygame.Color(0, 50, 0, 255)
        for x in range(0, height, 10):
            pygame.draw.line(self.grid_surface, color, (x, 0), (x, height), 1)
        for y in range(0, width, 10):
            pygame.draw.line(self.grid_surface, color, (0, y), (width, y), 1)
        # thicker lines through origin
        color = pygame.Color(0, 100, 0, 255)
        pygame.draw.line(self.grid_surface, color, (width / 2, 0), (width / 2, height))
        pygame.draw.line(self.grid_surface, color, (0, height / 2), (width, height / 2))
        self.draw_surface.blit(self.grid_surface, (0, 0))

    def draw_motors(self):
        """
        paints motors on surface
        origin for plotter is in the middle / bottom of the page, thats (0,0)
        """
        self.plot_surface.fill((0, 0, 0))
        position_a = (15, 0)
        position_b = (self.plot_surface.get_width() - 15, 0)
        pygame.draw.circle(self.plot_surface, (255, 255, 255), position_a, 15, 1)
        pygame.draw.circle(self.plot_surface, (255, 255, 255), position_b, 15, 1)
        pygame.draw.line(self.plot_surface, (255, 0, 0), position_a, self.new_position, 1)
        pygame.draw.line(self.plot_surface, (0, 0, 255), position_b, self.new_position, 1)
        self.draw_surface.blit(self.plot_surface, (0, 0))

    def draw_pen(self):
        """
        paints motors on surface
        origin for plotter is in the middle / bottom of the page, thats (0,0)
        """
        # only if z > 0.0 use a solid color
        pygame.draw.line(self.pen_surface, self.pen_color, self.old_position, self.new_position, 1)
        self.draw_surface.blit(self.pen_surface, (0, 0))

    def draw_text(self):
        font_height = self.font.get_height()
        textcolor = (255, 255, 255)
        self.text_surface.fill((0, 0, 0))
        text = self.font.render("Max-X : %0.2f" % self.controller.stats.max_x, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 0 + 1))
        text = self.font.render("Max-Y : %0.2f" % self.controller.stats.max_y, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 1 + 1))
        text = self.font.render("Width : %05s" % self.width, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 2 + 1))
        text = self.font.render("Height: %05s" % self.height, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 3 + 1))
        text = self.font.render("Scale : %05s" % self.scale, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 4 + 1))
        text = self.font.render("Motor Positions:", 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 5 + 1))
        text = self.font.render("X     : %05s" % (self.controller.motors["X"].position * self.scale), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 6 + 1))
        text = self.font.render("Y     : %05s" % (self.controller.motors["Y"].position * self.scale), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 7 + 1))
        text = self.font.render("Z     : %05s" % (self.controller.motors["Z"].position * self.scale), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 8 + 1))
        text = self.font.render("Tranformer Positions:", 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 9 + 1))
        text = self.font.render("A     : %05s" % self.controller.transformer.A, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 10 + 1))
        text = self.font.render("B     : %05s" % self.controller.transformer.B, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 11 + 1))
        text = self.font.render("Controller Positions:", 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 12 + 1))
        text = self.font.render("X: %0.2f" % self.controller.position.X, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 13 + 1))
        text = self.font.render("Y: %0.2f" % self.controller.position.Y, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 14 + 1))
        text = self.font.render("Z: %0.2f" % self.controller.position.Z, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 15 + 1))
        text = self.font.render("C-Steps: %05s" % self.step_counter, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 16 + 1))
        text = self.font.render("P-Commands: %05s" % self.command_counter, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 17 + 1))
        text = self.font.render("Elapsed Time: %s s" % int(time.time() - self.start_time), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 18 + 1))
        text = self.font.render("Last Command", 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 19 + 1))
        text = self.font.render("%s" % self.parser.command, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 20 + 1))
 
    def update(self):
        """do pygame update stuff"""
        self.draw_surface.fill((0, 0, 0))
        self.draw_text()
        self.draw_grid()
        self.draw_motors()
        self.draw_pen()
        pygame.display.flip()
        # automatic stepping or keypress
        if self.automatic is False:
            while (pygame.event.wait().type != pygame.KEYDOWN):
                pass
