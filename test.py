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
    global pitch 
    global roll
    global yaw
    
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
        print(round(pitch),round(roll),round(yaw)) #TODO: Do something with the data

def main():
    data_daemon()
    
        
        
        

if __name__=='__main__':
    sys.exit(main())

    
    


