#!/usr/bin/python3

import sys
sys.path.insert(0,'/home/pi/mpu6050')
from mpu6050 import mpu6050
from py_qmc5883l import QMC5883L
import Proc_BigEasyDriver as pbed
import geomag
import time
import datetime as dt
import math
import threading
import csv
from get_data import IMU

#Initiate global pos
pos= [0,0,0]

def read_compensated_bearing(pitch,roll,x,z):
        '''
        Compensate bearing for pitch and roll
        Adapted from: https://github.com/bitify/raspi/blob/2619da30ec36b29e47baae9a65b89d19653b5ec2/i2c-sensors/bitify/python/sensors/hmc5883l.py#L91
        '''
        
        cos_pitch = (math.cos(pitch))
        sin_pitch = (math.sin(pitch))
        
        cos_roll = (math.cos(roll))
        sin_roll = (math.sin(roll))
    
        Xh = (x * cos_roll) + (z * sin_roll)
        Yh = (x * sin_pitch * sin_roll) + (z * cos_pitch) - (z * sin_pitch * cos_roll)
        
        bearing = math.atan2(Yh, Xh)
        if bearing < 0:
            return bearing + (2*math.pi)
        else:
            return bearing

def data_daemon():
    """Daemon computing the position as perceived by sensor"""
    global pos
    #[pitch,roll,yaw] = pos #TODO: See how well this works when all is aligned
    
    imu = IMU()
    next = dt.datetime.now()
    pos = imu.read_pitch_roll_yaw()
    while True:
        pos = imu.read_pitch_roll_yaw()
    

if __name__=='__main__':
    
    

    


class MountControl:
    """Class controling the telescope"""

    stepsize = 16#TODO:
    dec_rpm = 0.25/360
    
    def __init__(self) -> None:
        #Start thread for recording movement
        self.t = threading.Thread(data_daemon, daemon=True) #FIXME: Doesnt work
        self.t.start() #Figure out the below
        self.motor_alt = pbed.ProcBigEasyDriver(step, direction, ms1, ms2, ms3, enable, #Add pins
                                   microstepping=stepsize, rpm=dec_rpm, steps_per_rev=200,
                                   Kp=0.2, Ki=0.1) #What is Kp and Ki
        self.motor_alt.enable()
        self.motor_az = pbed.ProcBigEasyDriver(step, direction, ms1, ms2, ms3, enable,
                                   microstepping=stepsize, rpm=dec_rpm, steps_per_rev=200*16,
                                   Kp=0.2, Ki=0.1)
        self.motor_az.enable()

    def correct(self, alt, az):
        """Make correction to current coordinates"""
        rpm = 5
        dpm = rpm*360
        
        global pos
        #Save current position
        coord = pos
        #Time based indexing of rotation
        sec_for_rot = (az/dpm)*60
        t = dt.datetime.now()+dt.timedelta(seconds=sec_for_rot)
        self.motor_az.set_rpm(rpm)
        while dt.datetime.now() > t:
            pass
        self.motor_az.set_rpm(dec_rpm)
        #Time based indexing of rotation
        sec_for_rot = (alt/dpm)*60
        t = dt.datetime.now()+dt.timedelta(seconds=sec_for_rot)
        self.motor_alt.set_rpm(rpm)
        while dt.datetime.now() > t:
            pass
        self.motor_alt.set_rpm(dec_rpm)
        #Set global pos
        pos = coord
        return 0

    def rotate_az(self,deg):
        """Rotate Motor1 Az"""
        global pos
        #Change motor speed
        self.motor_az.set_rpm(5)

        new = pos[0]+deg
        while pos[0]!=new:
            pass
        #Reset rpm
        self.motor_az.set_rpm(dec_rpm)

        return 0

    def rotate_alt(self,deg):
        """Rotate Motor2 Alt
        -------------------------
        gets global pos for positional data as returned by data_daemon
        Modify coefficients!
        """
        global pos
        #Change motor speed
        self.motor_az.set_rpm(5)

        new = pos[1]]+deg
        while pos[1]!=new:
            pass
        #Reset rpm
        self.motor_az.set_rpm(dec_rpm)
        
        return 0
    
    def go_to_object(self,obj)

    def stop(self):
        """Stops measurements and motors"""
        self.motor_alt.stop()
        self.motor_az.stop()
        self.t.stop()

        

