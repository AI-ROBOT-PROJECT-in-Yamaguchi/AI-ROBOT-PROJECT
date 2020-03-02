#!/usr/bin/python
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
#   0 : 0 : x (left = -1.0, right = 1.0)
#       1 : y (up = 1.0, down = -1.0)

import os
import pygame
import math
import RPi.GPIO as GPIO
import numpy as np
import time

import traceback
import sys
import signal
import subprocess

class PS4Controller(object):
    controller = None
    axis_data = {0:0.0, 1:0.0, 2:-1.0, 3:0.0, 4:0.0, 5:-1.0}
    button_data = None
    hat_data = None
    right_angle = -1.0
    left_angle = -1.0
    up_l_p = 26
    up_l_m = 19
    up_r_p = 13
    up_r_m = 6
    low_l_p = 5
    low_l_m = 11
    low_r_p = 22
    low_r_m = 27
    pin_motor = [26,19,13,6,5,11,22,27]
    status = [True,True,True,True,True,True,True,True]
    pwm_motor = []
    #         up_l  up_r  do_l  do_r
    speed = [[1500,1500,1500,1500,1300,1300,1200,1200],     #fast
            [ 3500,3500,3500,3500,3300,3300,2500,2500],
            [ 5500,5500,6300,6300,5000,5000,2900,2900]      #slow
            ]
    '''
    relation sleep and speed
    sleep:0.001  -> speed:500 900 1300 1700 2100 more slow 
    sleep:0.0001 -> speed:1500 2000 2500 3000 3500
    sleep:0.0001 -> speed:1500 3500 5500
    '''
    move = False
    count = 0
    check_speed = 1
    def __init__(self, servo):
        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        self.servo = servo
        for pin in self.pin_motor:
            GPIO.setup(pin,GPIO.OUT)
        
        for pin,speed in zip(self.pin_motor,self.speed[self.check_speed]):
            pwm = GPIO.PWM(pin,speed)
            pwm.start(100)
            self.pwm_motor.append(pwm)
        
    def listen(self):
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
        
        i = 0
        flag1 = False
        flag6 = False
        flag7 = False

        while True:
            time.sleep(0.0001)
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    self.axis_data[event.axis] = round(event.value,2)
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.button_data[event.button] = True
                elif event.type == pygame.JOYBUTTONUP:
                    self.button_data[event.button] = False
                elif event.type == pygame.JOYHATMOTION:
                    self.hat_data[event.hat] = event.value
                #print(self.button_data[1])
                
                #print(self.button_data)
                #print(self.axis_data)
                #print(self.hat_data)
            
            #get O button and attack motor
            if self.button_data[1] and flag1 != self.button_data[1]:
               self.servo.start(0)
               self.servo_angle(-50)
               time.sleep(0.6)
               self.servo_angle(60)
               time.sleep(0.1)
               self.servo.ChangeDutyCycle(0)
            flag1 = self.button_data[1]
            
            #get joystick
            '''
            #left joystick
            if self.distance(0,1) > 0.75 and self.distance(0,1) < 1.25:
                self.left_angle = self.left_controller_angle()
            else :
                self.left_angle = -1.0
            '''
            #right joystick 
            if self.distance(3,4) > 0.75 and self.distance(3,4) < 1.25:
                self.right_angle = self.right_controller_angle()
            else:
                self.right_angle = -1.0
    
            #get L2 button and speed down
            if self.button_data[6] and flag6 != self.button_data[6]: #more slow
                if self.check_speed != 2:
                    self.check_speed += 1
                    for pwm,speed in zip(self.pwm_motor,self.speed[self.check_speed]):
                        pwm.ChangeFrequency(speed)
                        #pwm.ChangeDutyCycle()
            flag6 = self.button_data[6]

            #get R2 button and speed up
            if self.button_data[7] and flag7 != self.button_data[7]: #more fast
                if self.check_speed != 0:
                    self.check_speed -= 1
                    for pwm,speed in zip(self.pwm_motor,self.speed[self.check_speed]):
                        pwm.ChangeFrequency(speed)
                        #pwm.ChangeDutyCycle()
            flag7 = self.button_data[7]
            print('speed',self.check_speed)

            #get closs key and move 
            if self.right_angle != -1.0:         #round
                self.send_rightjoy_command()
                self.move = True
                self.count = 0
            elif self.hat_data[0][0] == -1.0:     #left
                print('push left')
                self.status = [False,True,True,False,True,False,False,True]
                self.move = True
                self.count = 0
            elif self.hat_data[0][0] == 1.0:      #right
                print('push right')
                self.status = [True,False,False,True,False,True,True,False]
                self.move = True
                self.count = 0
            elif self.hat_data[0][1] == 1.0:      #up
                print('push up')
                self.status = [True,False,True,False,True,False,True,False]
                self.move = True
                self.count = 0
            elif self.hat_data[0][1] == -1.0:     #down
                print('push down')
                self.status = [False,True,False,True,False,True,False,True]
                self.move = True
                self.count = 0
            else:
                print('stop')
                self.status = [False,False,False,False,False,False,False,False]
                self.move = False
            
            #Status Verrification
            for pin,state in zip(self.pin_motor,self.status):
                print('{p}:{s} '.format(p=pin,s=state),end='')
            print()
            
            #output
            if self.move:
                for pin,state in zip(self.pin_motor,self.status):
                    GPIO.output(pin,state)
            else:
                for pin,state in zip(self.pin_motor,self.status):
                    state = not state
                    GPIO.output(pin,state)
                #    self.count += 1
                #if count >= 3:  #and if stop status -> comment  
                #    self.status = [False,False,False,False,False,False,False,False]
                #    self.count = 0

    
    def servo_angle(self, angle):
        duty = 2.5 + (12.0-2.5) * (angle+90) / 180
        self.servo.ChangeDutyCycle(duty)
    '''
    def left_controller_angle(self):
        y_deg = math.degrees(math.asin(self.axis_data[1]))
        if self.axis_data[0] >= 0:
            if self.axis_data[1] < 0:
                return -y_deg
            else:
                return 360.0 - y_deg
        else:
            return 180 + y_deg
    '''
    def right_controller_angle(self):
        y_deg = math.degrees(math.asin(self.axis_data[4]))
        
        if self.axis_data[3] >= 0:
            if self.axis_data[4] < 0:
                return -y_deg
            else:
                return 360.0 - y_deg
        else:
            return 180 + y_deg

    def distance(self,x,y):
        return math.sqrt(pow(0-self.axis_data[x],2)+pow(0-self.axis_data[y],2))
        
    #rotate
    def send_rightjoy_command(self):
        rad = math.radians(self.right_angle)
        #right side
        if math.cos(rad) >= math.sqrt(3)/2:
            rate = 7.1*math.cos(rad)-6.1  # 0 ~ 1 speed rate near 0
            speed = rate * 255
            print("right_rotate:",speed)
            self.status = [True,False,False,True,True,False,False,True]
        #left side
        elif math.cos(rad) <= -math.sqrt(3)/2:
            rate = 7.1*-math.cos(rad)-6.1  # 0 ~ 1 speed rate near 180
            speed = rate * 255
            print("left_rotate:",speed)
            self.status = [False,True,True,False,False,True,True,False]
    '''
    #move
    def send_leftjoy_command(self):
        rad = math.radians(self.left_angle)
        
        inv_b = np.array([[math.sin(rad),math.cos(rad)],
                        [ math.sin(rad),-math.cos(rad)],
                        [ math.sin(rad),-math.cos(rad)],
                        [ math.sin(rad), math.cos(rad)]])
        v = np.array([abs(math.sin(rad))*255,abs(math.cos(rad))*255])
        
        speed = np.dot(inv_b,v)
        #print("m1:",speed[0],"m2:",speed[1],"m3:",speed[2],"m4:",speed[3])
        
        sp = []
        sm = []
        for s in speed:
            if s == 255:
                sp.append(True)
                sm.append(False)
            elif s == -255:
                sp.append(False)
                sm.append(True)
            else:
                sp.append(True)
                sm.append(True)
        print('motor1:',sp[0],',',sm[0],',motor2',sp[1],',',sm[1],'motor3',sp[2],',',sm[2],'motor4',sp[3],',',sm[3])
        GPIO.output(self.up_l_p,sp[0])
        GPIO.output(self.up_l_m,sm[0])
        GPIO.output(self.up_r_p,sp[1])
        GPIO.output(self.up_r_m,sm[1])
        GPIO.output(self.low_l_p,sp[2])
        GPIO.output(self.low_l_m,sm[2])
        GPIO.output(self.low_r_p,sp[3])
        GPIO.output(self.low_r_m,sm[3])
            ''' 
def blue():
    return subprocess.run(["l2ping","90:89:5F:01:71:DE","-c","1"]).returncode == 0

signal.signal(signal.SIGHUP,signal.SIG_IGN)
print("Invoked.",file=sys.stderr)
try:
    print("ps4-controler invoked.",file=sys.stderr)
    print("Searching bluetooth device...",file=sys.stderr)
    while not blue():
        time.sleep(1)
    print("Bluetooth device found.",file=sys.stderr)
    spin = 17
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(spin, GPIO.OUT)
    print("GPIO setup finished.",file=sys.stderr)
    servo = GPIO.PWM(spin, 50)
    servo.start(0)
    print("Servo starts.",file=sys.stderr)
    ps4 = PS4Controller(servo)
    ps4.listen()
except Exception as e:
    print(traceback.format_exc())
