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
#Variable to store [pitch,roll] every 10 seconds
perm = [['IntGyrx','IntGyry','pitch','pitch_acc','roll','roll_acc']]
dt = 0.01 #Sampling rate

def ComplementaryFilter(acc, gyr):
    global pitch
    global coeff #FIXME: Dont need roll but yaw
    global roll
    #Integrate gyroscope data
    pitch += gyr[0]*dt
    roll -= gyr[1]*dt
    app=[gyr[0]*dt,gyr[1]*dt,0,0,0,0]
    #Compensate for drift with accelerometer data if the drift is significant
    force_mag = sum([abs(i) for i in acc]) #Data is already normalized, so this is technically total acc
    #Most likely we will be using the 2G range as no higher is required
    #FIXME: values, will depend on sidereal speed
    if 0>force_mag>2*9.81: #Check that value is within two g
        #Get y-axis rot
        pitch_acc = math.atan2(acc[1]/acc[2])*180/math.pi
        pitch = pitch*coeff[0]+pitch_acc*coeff[1]
        #Get x-axis rot
        roll_acc = math.atan2(acc[0]/acc[2])*180/math.pi
        roll = roll*coeff[0]+roll_acc*coeff[1]
        app=[gyr[0]*dt,gyr[1]*dt,pitch,pitch_acc,roll,roll_acc]
    perm.append(app)


def return_list(dict):
    x = dict['x']
    y = dict['y']
    z = dict['z']
    return [x,y,z]

def startTimer(lim):
    if lim:
        if len(perm) == lim:
            return 0
    threading.Timer(dt, startTimer, [1000]).start()
    ComplementaryFilter(return_list(sensor.get_accel_data()), return_list(sensor.get_gyro_data()))
    

def main():
    sensor.set_accel_range(sensor.ACCEL_RANGE_2G)
    print('Dont move, data collection start in 2 seconds')
    time.sleep(2)
    #Collect acc data without movement
    startTimer(lim=1000)
    with open('test_data', 'w') as file:
        for i in perm:
            file.writelines(str(i))
    '''measure = threading.Thread(group=None, target=startTimer,daemon=True)
    measure.start()
    res = input('Press enter after rotating 90 degrees')'''


if __name__=='__main__':
    sys.exit(main())

    
    


