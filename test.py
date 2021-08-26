#!/usr/bin/python3

import sys
sys.path.insert(0,'/home/pi/mpu6050')
from mpu6050 import mpu6050
import time
import math

sensor = mpu6050(0x68)

orientation = [0,0,0]

def compute_rotation(gyro,correction):
    """Compute rotation in timestep --- small angle approximation"""
    x = gyro['x']-correction[0]
    y = gyro['y']-correction[1]
    z = gyro['z']-correction[2]
    y_rot = -math.atan2(x, math.sqrt(y**2+z**2))
    x_rot = math.atan2(y, math.sqrt(x**2+z**2))
    orientation[0] += math.degrees(x_rot)
    orientation[1] += math.degrees(y_rot)


sensor.set_accel_range(sensor.ACCEL_RANGE_2G)

#Get normalization
[x,y,z] =[0,0,0]
for i in range(10):
    print('Dont move')
    gyro = sensor.get_gyro_data()
    x += gyro['x']
    y += gyro['y']
    z += gyro['z']
    x = x/10
    y = y/10
    z = z/10



while True:
    time.sleep(1)
    compute_rotation(sensor.get_gyro_data(),correction=[x,y,z])
    print(orientation)
    
    '''
    print('Acceleration')
    print(sensor.get_accel_data())
    print('Temperature')
    print(sensor.get_temp())
    print('Gyro')
    print(sensor.get_gyro_data())
    '''


