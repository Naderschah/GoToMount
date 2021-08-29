#!/usr/bin/python3

import sys
sys.path.insert(0,'/home/pi/mpu6050')
from mpu6050 import mpu6050
import time
import math
import threading
import csv

sensor = mpu6050(0x68)
pitch = 0 
roll = 0
yaw = 0

def return_list(dict):
    x = dict['x']
    y = dict['y']
    z = dict['z']
    return [x,y,z]

def data_daemon():
    """Daemon computing the position as perceived by sensor"""
    global pos
    [pitch,roll,yaw] = pos
    
    sensor.set_accel_range(sensor.ACCEL_RANGE_2G)
    sensor.set_gyro_range(sensor.GYRO_RANGE_250DEG)
    last_time = time.time()

    while True:
        acc=return_list(sensor.get_accel_data(g=True))
        gyr=return_list(sensor.get_gyro_data())
        dt = time.time()-last_time
        last_time = time.time()

        pitch += gyr[0]*dt
        roll += gyr[1]*dt
        yaw += gyr[2]*dt

        force_mag = math.sqrt(acc[0]**2+acc[1]**2+acc[2]**2)
        #Only use if data around 1g
        if 0.9<force_mag<1.1:
            pitch = pitch*0.95  + math.atan2(acc[0], math.sqrt(acc[1]**2 + acc[2]**2)) *180/math.pi *0.05
            roll = roll*0.95 + math.atan2(-acc[1], math.sqrt(acc[0]**2+acc[2]**2))*180/math.pi *0.05
            yaw = yaw*0.95 + math.atan2(acc[2], math.sqrt(acc[0]**2+acc[2]**2))*180/math.pi*0.05 
            #FIXME: Use magnetometer to fuse the data (1-weight)*gyro+weight*magnetometer
        pos = [pitch,roll,yaw] #Can we remove roll? Probably but check
    
        
        
        

if __name__=='__main__':
    

    


#Orientation as perceived by MPU
pos = [0,0,0]

class MountControl:
    """Class controling the telescope"""

    stepsize = 1#TODO:
    
    def __init__(self) -> None:
        self.MPU = mpu6050(0x68)
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

        


    def 


