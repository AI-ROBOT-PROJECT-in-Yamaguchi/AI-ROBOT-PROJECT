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
from fftest import fftest3

class PS4Controller(object):
    controller = None
    axis_data = {0:0.0, 1:0.0, 2:-1.0, 3:0.0, 4:0.0, 5:-1.0}
    button_data = None
    hat_data = None
    right_angle = -1.0
    left_angle = -1.0
    pin_servo = 17
    pwm_servo = None
    pin_motor = [26,19,13,6,5,11,22,27]
    status = [True,True,True,True,True,True,True,True]
    pwm_motor = []
    #         up_l      up_r      do_l      do_r
    speed = [[1500,1500,1500,1500,1300,1300,1200,1200],     #fast
            [ 3500,3500,3500,3500,3300,3300,2500,2500],
            [ 5500,5500,6300,6300,5000,5000,2900,2900]      #slow
            ]
    speed_rate = [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
    move = False
    count = 0
    now_speed = 1
    flag1 = False
    flag3 = False
    flag6 = False
    flag7 = False
    pid_m = 0
    pid_m1 = 0
    pid_e = 0
    pid_e1 = 0
    pid_e2 = 0
    pid_kp = 0.003
    pid_ki = 0.003
    pid_kd = 0.003
    pid_goal = 1
    fftest = None

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_servo, GPIO.OUT)
        self.pwm_servo = GPIO.PWM(self.pin_servo, 50)
        self.pwm_servo.start(0)
        for pin in self.pin_motor:
            GPIO.setup(pin,GPIO.OUT)
            GPIO.output(pin,False)
        for pin,speed in zip(self.pin_motor,self.speed[self.now_speed]):
            pwm = GPIO.PWM(pin,speed)
            pwm.start(100)
            self.pwm_motor.append(pwm)

        print("Searching bluetooth device...",file=sys.stderr)
        while not self.blue():
            time.sleep(1)
        print("Bluetooth device found.",file=sys.stderr)
        pygame.init()
        pygame.joystick.init()
        while pygame.joystick.get_count() == 0:
            time.sleep(0.5)
        print("joystick device get")
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        self.fftest = fftest3.Vibration()
    
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

        while True:
            time.sleep(0.0001)
            self.speed_rate = [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
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
            
            #get O button and move motor
            self.move_servo()
            
            #get aquare button and vibration
            #self.vibration()
            
            #get speed status
            self.get_speed_status()
            #print('speed',self.now_speed)
            
            #get motor status
            self.get_motor_status()
            
            #Status Verrification
            #for pin,state in zip(self.pin_motor,self.status):
            #    print('{p}:{s} '.format(p=pin,s=state),end='')
            #print()
            
            #output
            self.send_command()
            #print(self.pid_m)
   
    def blue(self):
        return subprocess.run(["l2ping","90:89:5F:01:71:DE","-c","1"]).returncode == 0
    
    def servo_angle(self, angle):
        duty = 2.5 + (12.0-2.5) * (angle+90) / 180
        self.pwm_servo.ChangeDutyCycle(duty)

    def move_servo(self):
        #get O button and attack motor
        if self.button_data[1] and self.flag1 != self.button_data[1]:
            self.pwm_servo.start(0)
            self.servo_angle(-50)
            time.sleep(0.6)
            self.servo_angle(60)
            time.sleep(0.1)
            self.pwm_servo.ChangeDutyCycle(0)
        self.flag1 = self.button_data[1]

    def vibration(self):
        #if self.button_data[3] and self.flag3 != self.button_data[3]:
        #    self.fftest.move(1)
        #self.flag3 = self.button_data[3]
        self.fftest.move(1)

    def left_controller_angle(self):
        y_deg = math.degrees(math.asin(self.axis_data[1]))
        if self.axis_data[0] >= 0:
            if self.axis_data[1] < 0:
                return -y_deg
            else:
                return 360.0 - y_deg
        else:
            return 180 + y_deg

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
    
    def get_speed_status(self):
        #L2 button -> slow
        if self.button_data[6] and self.flag6 != self.button_data[6]:
            if self.now_speed != 2:
                self.vibration()
                self.now_speed += 1
        self.flag6 = self.button_data[6]
        
        #R2 button -> fast
        if self.button_data[7] and self.flag7 != self.button_data[7]:
            if self.now_speed != 0:
                self.vibration()
                self.now_speed -= 1
        self.flag7 = self.button_data[7]

    #get status
    def get_motor_status(self):
        #left joystick
        if self.distance(0,1) > 0.95:
            self.left_angle = self.left_controller_angle()
        else :
            self.left_angle = -1.0

        #right joystick 
        if self.distance(3,4) > 0.95:
            self.right_angle = self.right_controller_angle()
        else:
            self.right_angle = -1.0

        if self.right_angle != -1.0:         #rotate
            self.set_rightjoy_command()
            self.move = True
            #self.count = 0
        elif self.left_angle != -1.0:        #move
            self.set_leftjoy_command()
            self.move = True
            #self.count = 0
        elif self.hat_data[0][0] == -1.0:     #left
            #print('push left')
            self.status = [False,True,True,False,True,False,False,True]
            self.move = True
            #self.count = 0
        elif self.hat_data[0][0] == 1.0:      #right
            #print('push right')
            self.status = [True,False,False,True,False,True,True,False]
            self.move = True
            #self.count = 0
        elif self.hat_data[0][1] == 1.0:      #up
            #print('push up')
            self.status = [True,False,True,False,True,False,True,False]
            self.move = True
            #self.count = 0
        elif self.hat_data[0][1] == -1.0:     #down
            #print('push down')
            self.status = [False,True,False,True,False,True,False,True]
            self.move = True
            #self.count = 0
        else:
            #print('stop')
            self.status = [False,False,False,False,False,False,False,False]
            self.move = False
        
    #rotate
    def set_rightjoy_command(self):
        rad = math.radians(self.right_angle)
        #right side
        if math.cos(rad) >= math.sqrt(3)/2:
            rate = 7.1*math.cos(rad)-6.1  # 0 ~ 1 speed rate near 0
            #speed = rate * 255
            #print("joy right rotate")
            self.status = [True,False,False,True,True,False,False,True]
        #left side
        elif math.cos(rad) <= -math.sqrt(3)/2:
            rate = 7.1*-math.cos(rad)-6.1  # 0 ~ 1 speed rate near 180
            #speed = rate * 255
            #print("joy left rotate")
            self.status = [False,True,True,False,False,True,True,False]

    #move
    def set_leftjoy_command(self):
        rad = math.radians(self.left_angle)
        
        inv_b = np.array([[math.sin(rad),math.cos(rad)],
                        [ math.sin(rad), math.cos(rad)],
                        [ math.sin(rad),-math.cos(rad)],
                        [ math.sin(rad),-math.cos(rad)],
                        [ math.sin(rad),-math.cos(rad)],
                        [ math.sin(rad),-math.cos(rad)],
                        [ math.sin(rad), math.cos(rad)],
                        [ math.sin(rad), math.cos(rad)]])
        v = np.array([abs(math.sin(rad)),abs(math.cos(rad))])   #-1 ~ 1
        
        speed = np.dot(inv_b,v)
        speed = 1.5 - abs(speed)
        self.speed_rate = speed
        #print("m1:",speed[0],"m2:",speed[1],"m3:",speed[2],"m4:",speed[3])
        if rad < math.pi/4 or rad >= 7*math.pi/4:
            #print('joy move right')
            self.status = [True,False,False,True,False,True,True,False]
        elif math.pi/4 <= rad and rad < 3*math.pi/4:
            #print('joy move up')
            self.status = [True,False,True,False,True,False,True,False]
        elif 3*math.pi/4 <= rad and rad < 5*math.pi/4:
            #print('joy move left')
            self.status = [False,True,True,False,True,False,False,True]
        elif 5*math.pi/4 <= rad and rad < 7*math.pi/4:
            #print('joy move down')
            self.status = [False,True,False,True,False,True,False,True]
    def set_pid(self):
        if self.pid_m < 1 and self.now_speed == 0:
            self.pid_m1 = self.pid_m
            self.pid_e2 = self.pid_m1
            self.pid_e1 = self.pid_e
            self.pid_e = self.pid_goal - self.pid_m
            self.pid_m = self.pid_m1 + self.pid_kp * (self.pid_e - self.pid_e1) + self.pid_ki * self.pid_e + self.pid_kd * ((self.pid_e - self.pid_e1)-(self.pid_e1 - self.pid_e2))
        else:
           self.pid_m = 1.0
    def reset_pid(self):
        self.pid_m = 0
        self.pid_m1 = 0
        self.pid_e = 0
        self.pid_e1 = 0
        self.pid_e2 = 0
        self.pid_kp = 0.003
        self.pid_ki = 0.003
        self.pid_kd = 0.003
        self.pid_goal = 1
    
    def send_command(self):
        #omni
        if self.move:
            self.set_pid()
            for pin,state in zip(self.pin_motor,self.status):
                GPIO.output(pin,state)
        else:
            self.reset_pid()
            for pin,state in zip(self.pin_motor,self.status):
                state = not state
                GPIO.output(pin,state)
            #    self.count += 1
            #if count >= 3:  #and if stop status -> comment  
            #    self.status = [False,False,False,False,False,False,False,False]
            #    self.count = 0
        #pwm
        for pwm,speed,rate in zip(self.pwm_motor,self.speed[self.now_speed],self.speed_rate):
            print(speed*rate*(6-self.pid_m*5),end=' ')
            pwm.ChangeFrequency(speed*rate*(3-self.pid_m*2))
        print()


signal.signal(signal.SIGHUP,signal.SIG_IGN)
print("Invoked.",file=sys.stderr)
try:
    ps4 = PS4Controller()
    #print("ps4-controler invoked.",file=sys.stderr)
    ps4.listen()
except Exception as e:
    print(traceback.format_exc())
