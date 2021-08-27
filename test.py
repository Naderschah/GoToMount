#!/usr/bin/python3

import sys
sys.path.insert(0,'/home/pi/mpu6050')
from mpu6050 import mpu6050
import time
import math
import threading

sensor = mpu6050(0x68)
#Coefficients to use for complementary filter
coeff = [0.98,0.02]
pitch = 0
roll = 0

dt = 0.01 #Sampling rate

def ComplementaryFilter(acc, gyr):
    global pitch
    global coeff
    global roll
    #Integrate gyroscope data
    pitch += gyr[0]*dt
    roll -= gyr[1]*dt

    #Compensate for drift with accelerometer data if the drift is significant
    force_mag = sum([abs(i) for i in acc]) #Data is already normalized, so this is technically total acc
    #Most likely we will be using the 2G range as no higher is required
    #FIXME: values, will depend on sidereal speed
    if 0>force_mag>2*9.81: #Check that value is within two g
        #Get y-axis
        pitch_acc = math.atan2(acc[1]/acc[2])*180/math.pi
        pitch = pitch*coeff[0]+pitch_acc*coeff[1]
        #Get x-axis
        roll_acc = math.atan2(acc[0]/acc[2])*180/math.pi
        roll = roll*coeff[0]+roll_acc*coeff[1]

def return_list(dict):
    x = dict['x']
    y = dict['y']
    z = dict['z']
    return [x,y,z]

def startTimer():
    threading.Timer(dt, startTimer)
    ComplementaryFilter(return_list(sensor.get_accel_data()), return_list(sensor.get_gyro_data()))
    print('pitch: {}, roll: {}'.format(pitch, roll))

def main():
    sensor.set_accel_range(sensor.ACCEL_RANGE_2G)
    startTimer()
    


if __name__=='__main__':
    sys.exit(main())

    
    


