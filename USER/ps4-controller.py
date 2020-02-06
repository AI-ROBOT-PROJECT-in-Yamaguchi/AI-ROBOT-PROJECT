#input id 
#
#button_data   (push = true release = false)
#   0 : X   
#   1 : O 
#   2 : triangle  
#   3 : square  
#   4 : L1 
#   5 : R1 
#   6 : L2 
#   7 : R2 
#   8 : SHARE 
#   9 : OPTIONS
#   10: PS 
#   11: push left joystick
#   12: push right joystick
#
#axis_data
#   0 : left joystick x     (left = -1 < x < 1 = right)
#   1 : left joystick y     (up = -1 < y < 1 = down)
#   2 : L2                  (push = 1.0 <   < -1.0 = release)
#   3 : right joystick x    (left = -1 < x < 1 = right)
#   4 : right joystick y    (up = -1 < y < 1 = down)
#   5 : R2                  (push = 1.0 <   < -1.0 = release)
#
#hat_data
#   0 : 0 : x (left = -1.0,right = 1.0)
#       1 : y (up = 1.0, down = -1.0)

import os
import pygame
import math

class PS4Controller(object):
    controller = None
    axis_data = None
    button_data = None
    hat_data = None

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

    def listen(self):
        right_angle = 0.0
        left_angle = 0.0
        if not self.axis_data:
            self.axis_data = {}

        if not self.button_data:
            self.button_data = {}
            for i in range(self.controller.get_numbuttons()):
                self.button_data[i] = False

        if not self.hat_data:
            self.hat_data = {}
            for i in range(self.controller.get_numhats()):
                self.hat_data[i] = (0, 0)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    self.axis_data[event.axis] = round(event.value,2)
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.button_data[event.button] = True
                elif event.type == pygame.JOYBUTTONUP:
                    self.button_data[event.button] = False
                elif event.type == pygame.JOYHATMOTION:
                    self.hat_data[event.hat] = event.value
                
                #print(self.button_data)
                #print(self.axis_data)
                #print(self.hat_data)

            if len(self.axis_data) >= 4:
                #left joystick
                if self.distance(0,1) > 0.75 and self.distance(0,1) < 1.25:
                    left_angle = self.left_controller_angle()
                else :
                    left_angle = -1

                #right joystick 
                if self.distance(3,4) > 0.75 and self.distance(3,4) < 1.25:
                    right_angle = self.right_controller_angle()
                else:
                    right_angle = -1
                print("left:",left_angle,"right:",right_angle)
            
    def left_controller_angle(self):
        x_deg = math.degrees(math.acos(self.axis_data[0]))
        y_deg = math.degrees(math.asin(self.axis_data[1]))
        if y_deg < 0:
            return x_deg
        else:
            return 360.0 - x_deg

    def right_controller_angle(self):
        x_deg = math.degrees(math.acos(self.axis_data[3]))
        y_deg = math.degrees(math.asin(self.axis_data[4]))
        if y_deg < 0:
            return x_deg
        else:
            return 360.0 - x_deg
        
    
    def distance(self,x,y):
        return math.sqrt(pow(0-self.axis_data[x],2)+pow(0-self.axis_data[y],2))


if __name__ == "__main__":
    ps4 = PS4Controller()
    ps4.listen()
