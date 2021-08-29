#!/usr/bin/python3

import sys
sys.path.insert(0,'/home/pi/mpu6050')
from mpu6050 import mpu6050
from py_qmc5883l import QMC5883L
import geomag
import time
import math
import threading
import csv
#Set up gyro and acc
MPU = mpu6050(0x68)
#Set up magnetometer
QMC = QMC5883L()
QMC.declination = geomag.declination(53.216667, 6.573889)

pitch = QMC.get_bearing()

pos= [pitch,0,0]

def return_list(dict):
    x = dict['x']
    y = dict['y']
    z = dict['z']
    return [x,y,z]


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
    [pitch,roll,yaw] = pos
    
    MPU.set_accel_range(MPU.ACCEL_RANGE_2G)
    MPU.set_gyro_range(MPU.GYRO_RANGE_250DEG)
    last_time = time.time()

    while True:
        acc=return_list(MPU.get_accel_data(g=True))
        gyr=return_list(MPU.get_gyro_data())
        dt = time.time()-last_time
        last_time = time.time()

        pitch += gyr[0]*dt
        roll += gyr[1]*dt
        yaw += gyr[2]*dt

        force_mag = math.sqrt(acc[0]**2+acc[1]**2+acc[2]**2)
        #Only use if data around 1g
        if 0.9<force_mag<1.1:
            pitch = pitch*0.95 + math.atan2(acc[0],math.sqrt(acc[1]**2+acc[2]**2))*180/math.pi *0.05
            roll = roll*0.95 + math.atan2(-acc[1], math.sqrt(acc[0]**2+acc[2]**2))*180/math.pi *0.05
            yaw = yaw*0.95 + math.atan2(acc[2], math.sqrt(acc[0]**2+acc[2]**2))*180/math.pi*0.05 
            pitch = read_compensated_bearing(pitch, roll,acc[0],acc[2])
        pos = [pitch,roll,yaw] #Can we remove roll? Probably but check
    
        
        
        

if __name__=='__main__':
    self.t = threading.Thread(data_daemon, daemon=True)
    self.t.start()
    while True:
        time.sleep(1)
        print(pos)
    

    


#Orientation as perceived by MPU
pos = [0,0,0]

class MountControl:
    """Class controling the telescope"""

    stepsize = 1#TODO:
    
    def __init__(self) -> None:
        #Start thread for recording movement
        self.t = threading.Thread(data_daemon, daemon=True)
        self.t.start()
        self.azalt = [0,0]
        self.get_az()

    def get_alt(self):
        """Get azimuth from magnetic field"""

    def rotate_az(self,deg):
        """Rotate Motor1 Az"""
        global pos

        new = self.altaz[1]+deg
        while self.altaz[1]!=new:
            #Reset position
            pos[0] = 0
            #Do step

            #Compute change
            self.altaz[1] += 0.95*self.stepsize + 0.05*pos[0] #pitch

        return 0

    def rotate_alt(self,deg):
        """Rotate Motor2 Alt
        -------------------------
        gets global pos for positional data as returned by data_daemon
        Modify coefficients!
        """
        global pos
        
        new = self.altaz[0]+deg
        while self.altaz[0]!=new:
            #Reset position
            pos[2] = 0
            #Do step

            #Compute change
            self.altaz[0] += 0.95*self.stepsize+0.05*pos[2] #yaw
        
        return 0

        

