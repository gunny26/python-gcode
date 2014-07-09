#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""Module to simulate a plotter"""
import sys
import threading
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
import pygame
import time
# own modules
# from Point3d import Point3d as Point3d


class LaserSimulator(threading.Thread):
    """Pygame Simulation of Laser Engraver, derived from PlotterSimulator"""

    def __init__(self, controller, parser, automatic, zoom=1.0):
        """automatic inidcates whether the user has to press a key on ever update cycle"""
        threading.Thread.__init__(self)
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
        # to indicate that this thread should stop
        self.stop_flag = False
        # got into update loop
        self.set_controller(controller)
        self.set_parser(parser)
        self.start()

    def set_controller(self, controller):
        """called to set controller object"""
        self.controller = controller
        self.draw_scale = controller.transformer.get_scale()
        self.new_position = (0, 0)
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
        if self.controller.position.Z < 5.0 :
            self.pen_color = (0, 255, 0)
        transformed = self.controller.position * self.draw_scale * self.zoom
        self.new_position = (transformed.X, transformed.Y)
        self.update()

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

    def update_controller(self):
        """
        paints motors on surface
        origin for plotter is in the middle / bottom of the page, thats (0,0)
        """
        self.plot_surface.fill((0, 0, 0))
        transformed = self.controller.position * self.draw_scale * self.zoom
        # transformed = transformed + Point3d(0, 0, 0)
        position_x = (int(transformed.X), 15)
        position_x_end = (int(transformed.X), self.plot_surface.get_height())
        position_y = (15, int(transformed.Y))
        position_y_end = (self.plot_surface.get_width(), int(transformed.Y))
        pygame.draw.circle(self.plot_surface, (255, 255, 255), position_x, 15, 1)
        pygame.draw.line(self.plot_surface, (0, 255, 0), position_x, position_x_end, 1)
        pygame.draw.circle(self.plot_surface, (255, 255, 255), position_y, 15, 1)
        pygame.draw.line(self.plot_surface, (0, 0, 255), position_y, position_y_end, 1)

    def update_tool(self):
        """
        paints motors on surface
        origin for plotter is in the middle / bottom of the page, thats (0,0)
        dont blank this surface on every update
        """
        # only if z > 0.0 use a solid color
        pygame.draw.line(self.pen_surface, self.pen_color, self.old_position, self.new_position, 1)

    def update_text(self):
        """display textual informations"""
        text_list = []
        text_list.append("Parser Informations")
        text_list.append(" Commands: %05s" % self.command_counter)
        text_list.append(" Last Command")
        text_list.append(" %s" % self.parser.command)
        text_list.append("Max-X : %0.2f" % self.controller.stats.max_x)
        text_list.append("Max-Y : %0.2f" % self.controller.stats.max_y)
        text_list.append("Scale : %05s" % self.draw_scale)
        text_list.append("Motor Informations")
        text_list.append(" X = %05s" % (self.controller.motors["X"].position * self.draw_scale))
        text_list.append(" Y = %05s" % (self.controller.motors["Y"].position * self.draw_scale))
        text_list.append(" Z = %05s" % (self.controller.motors["Z"].position * self.draw_scale))
        text_list.append("Controller Informations:")
        text_list.append(" X = %0.2f" % self.controller.position.X)
        text_list.append(" Y = %0.2f" % self.controller.position.Y)
        text_list.append(" Z = %0.2f" % self.controller.position.Z)
        text_list.append(" C-Steps: %05s" % self.step_counter)
        text_list.append("Elapsed Time: %s s" % int(time.time() - self.start_time))
        self.text_surface.fill((0, 0, 0))
        linecounter = 0
        textcolor = (255, 255, 255)
        for line in text_list:
            text = self.font.render(line, 1, textcolor)
            self.text_surface.blit(text, (0, self.font.get_height() * linecounter + 1)) 
            linecounter += 1

    def update_motors(self):
        # draw real motor positions
        motor_x = int(self.controller.motors["X"].position * self.zoom / self.controller.resolution)
        motor_y = int(self.controller.motors["Y"].position * self.zoom / self.controller.resolution)
        self.plot_surface.set_at((motor_x, motor_y), (255, 0, 0))
 
    def update(self):
        """data update loop called from callback methods"""
        # self.update_grid()
        self.update_controller()
        self.update_tool()
 
    def run(self):
        """do pygame update stuff in endless loop"""
        # draw grid surface only the first time, this surface will not change
        self.draw_grid()
        clock = pygame.time.Clock()
        while self.stop_flag is False:
            clock.tick(30) # not more than 60 frames per seconds
            events = pygame.event.get()  
            for event in events:  
                if event.type == pygame.QUIT:  
                    sys.exit(0)
            keyinput = pygame.key.get_pressed()
            if keyinput is not None:
                # print keyinput
                if keyinput[pygame.K_ESCAPE]:
                    sys.exit(1)
            self.draw_surface.fill((0, 0, 0))
            self.update_text()
            self.update_motors()
            # blit subsurfaces
            self.draw_surface.blit(self.grid_surface, (0, 0))
            self.draw_surface.blit(self.plot_surface, (0, 0))
            self.draw_surface.blit(self.pen_surface, (0, 0))
            pygame.display.update()
