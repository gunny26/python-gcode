#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""Module to simulate a plotter"""
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
import pygame
import time


class LaserSimulator(object):
    """Pygame Simulation of Laser Engraver, derived from PlotterSimulator"""

    def __init__(self, automatic, zoom=1.0):
        """automatic inidcates whether the user has to press a key on ever update cycle"""
        self.automatic = automatic
        self.zoom = zoom
        # initialize pygame
        pygame.init()
        pygame.display.set_caption("Laser Simulator")
        self.background = pygame.display.set_mode((1024, 600))
        # font to use in text surface
        self.font = pygame.font.Font(None, 28)
        self.text_surface = self.background.subsurface((0, 0, 324, 600))
        # drawing subsurface, where grid, plot and pen are blited to
        self.draw_surface = self.background.subsurface((324, 0, 700, 600))
        # surface to draw grid on
        self.grid_surface = pygame.Surface((700, 600))
        self.grid_surface.set_colorkey((0, 0, 0))
        self.grid_surface.fill((0, 0, 0))
        self.draw_surface.blit(self.grid_surface, (0, 0))
        # surface to draw the wires on
        self.plot_surface = pygame.Surface((700, 600))
        self.plot_surface.set_colorkey((0, 0, 0))
        self.plot_surface.fill((0, 0, 0))
        self.draw_surface.blit(self.plot_surface, (0, 0))
        # surface to draw the pen on
        self.pen_surface = pygame.Surface((700, 600))
        self.pen_surface.set_colorkey((0, 0, 0))
        self.pen_surface.fill((0, 0, 0))
        self.draw_surface.blit(self.pen_surface, (0, 0))
        # draw grid and display
        pygame.display.flip()
        self.draw_grid()
        # translation to move origin in the middle
        self.translate_x = 0
        self.translate_y = 0
        # controller related
        self.controller = None
        self.step_counter = 0
        self.scale = None
        self.old_position = None
        self.new_position = None
        self.draw_scale = None
        # parser related 
        self.parser = None
        self.command_counter = 0
        self.start_time = time.time()
        # pen related
        self.pen_color = (0, 0, 0)

    def set_controller(self, controller):
        """called to set controller object"""
        self.controller = controller
        self.draw_scale = controller.transformer.scale
        self.new_position = (self._taz_x(self.controller.position.X), self._taz_y(self.controller.position.Y))
        self.old_position = self.new_position

    def set_parser(self, parser):
        """called to set parser object"""
        self.parser = parser

    def controller_cb(self, *args):
        """called from controller to inform about changes"""
        self.old_position = self.new_position
        self.step_counter += 1
        # set pen color according to z position,
        # z below zero indicates drawing
        self.pen_color = (32, 32, 32)
        if self.controller.position.Z < 0.0 :
            self.pen_color = (0, 255, 0)
        self.new_position = (self._taz_x(self.controller.position.X), self._taz_y(self.controller.position.Y))
        self.update()

    def _taz_x(self, x):
        return(int(x * self.draw_scale * self.zoom + self.translate_x))

    def _taz_y(self, y):
        return(int(y * self.draw_scale * self.zoom + self.translate_y))

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
        self.grid_surface.fill((0, 0, 0))
        width = self.grid_surface.get_width()
        height = self.grid_surface.get_height()
        color = pygame.Color(0, 50, 0, 255)
        for x_steps in range(0, width, 10):
            pygame.draw.line(self.grid_surface, color, (x_steps, 0), (x_steps, height), 1)
        for y_steps in range(0, height, 10):
            pygame.draw.line(self.grid_surface, color, (0, y_steps), (width, y_steps), 1)
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
        position_x = (self._taz_x(self.controller.position.X), 15)
        position_x_end = (self._taz_x(self.controller.position.X), self.plot_surface.get_height())
        position_y = (15, self._taz_y(self.controller.position.Y))
        position_y_end = (self.plot_surface.get_width(), self._taz_y(self.controller.position.Y))
        pygame.draw.circle(self.plot_surface, (255, 255, 255), position_x, 15, 1)
        pygame.draw.line(self.plot_surface, (0, 255, 0), position_x, position_x_end, 1)
        pygame.draw.circle(self.plot_surface, (255, 255, 255), position_y, 15, 1)
        pygame.draw.line(self.plot_surface, (0, 0, 255), position_y, position_y_end, 1)
        self.draw_surface.blit(self.plot_surface, (0, 0))

    def draw_tool(self):
        """
        paints motors on surface
        origin for plotter is in the middle / bottom of the page, thats (0,0)
        dont blank this surface on every update
        """
        # only if z > 0.0 use a solid color
        pygame.draw.line(self.pen_surface, self.pen_color, self.old_position, self.new_position, 1)
        self.draw_surface.blit(self.pen_surface, (0, 0))

    def draw_text(self):
        """display textual informations"""
        font_height = self.font.get_height()
        textcolor = (255, 255, 255)
        self.text_surface.fill((0, 0, 0))
        text = self.font.render("Max-X : %0.2f" % self.controller.stats.max_x, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 0 + 1))
        text = self.font.render("Max-Y : %0.2f" % self.controller.stats.max_y, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 1 + 1))
        text = self.font.render("Scale : %05s" % self.draw_scale, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 2 + 1))
        text = self.font.render("Motor Positions:", 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 3 + 1))
        text = self.font.render("X     : %05s" % (self.controller.motors["X"].position * self.draw_scale), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 4 + 1))
        text = self.font.render("Y     : %05s" % (self.controller.motors["Y"].position * self.draw_scale), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 5 + 1))
        text = self.font.render("Z     : %05s" % (self.controller.motors["Z"].position * self.draw_scale), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 6 + 1))
        text = self.font.render("Controller Positions:", 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 7 + 1))
        text = self.font.render("X: %0.2f" % self.controller.position.X, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 8 + 1))
        text = self.font.render("Y: %0.2f" % self.controller.position.Y, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 9 + 1))
        text = self.font.render("Z: %0.2f" % self.controller.position.Z, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 10 + 1))
        text = self.font.render("C-Steps: %05s" % self.step_counter, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 11 + 1))
        text = self.font.render("P-Commands: %05s" % self.command_counter, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 12 + 1))
        text = self.font.render("Elapsed Time: %s s" % int(time.time() - self.start_time), 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 13 + 1))
        text = self.font.render("Last Command", 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 14 + 1))
        text = self.font.render("%s" % self.parser.command, 1, textcolor)
        self.text_surface.blit(text, (0, font_height * 15 + 1))
 
    def update(self):
        """do pygame update stuff"""
        self.draw_surface.fill((0, 0, 0))
        self.draw_text()
        self.draw_grid()
        self.draw_motors()
        self.draw_tool()
        pygame.display.flip()
        # automatic stepping or keypress
        if self.automatic is False:
            while (pygame.event.wait().type != pygame.KEYDOWN):
                pass
