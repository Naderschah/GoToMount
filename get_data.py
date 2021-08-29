## Modfied: https://github.com/bitify/raspi/blob/2619da30ec36b29e47baae9a65b89d19653b5ec2/i2c-sensors/bitify/python/sensors/imu.py



import time
from mpu6050 import mpu6050
from py_qmc5883l import QMC5883L
import geomag
import math


def return_list(dict):
    x = dict['x']
    y = dict['y']
    z = dict['z']
    return [x,y,z]

class IMU(object):
    
    K = 0.98
    K1 = 1 - K
    TWO_PI = (2*math.pi)
    
    def __init__(self):

        self.acc_gyro = mpu6050(0x68)
        self.compass = QMC5883L()
        self.compass.declination = geomag.declination(53.216667, 6.573889)

        self.last_time = time.time()
        self.time_diff = 0

        self.pitch = 0
        self.roll = 0
        # take a reading from the device to allow it to settle after config changes
        self.read_all()
        # now take another to act a starting value
        self.read_all()
        self.pitch = self.rotation_x
        self.roll = self.rotation_y

    def read_all(self):
        '''Return pitch and roll in radians and the scaled x, y & z values from the gyroscope and accelerometer'''
        self.gyroscope.read_raw_data()
        self.accelerometer.read_raw_data()
        
        [self.gyro_scaled_x,self.gyro_scaled_y,self.gyro_scaled_z] = return_list(self.acc_gyro.get_gyro_data())
        
        [self.accel_scaled_x,self.accel_scaled_y,self.accel_scaled_z] = return_list(self.acc_gyro.get_accel_data())
        
        self.rotation_x = self.read_x_rotation(self.accel_scaled_x, self.accel_scaled_y, self.accel_scaled_z)
        self.rotation_y = self.read_y_rotation(self.accel_scaled_x, self.accel_scaled_y, self.accel_scaled_z)
        
        now = time.time()
        self.time_diff = now - self.last_time
        self.last_time = now 
        (self.pitch, self.roll) = self.comp_filter(self.rotation_x, self.rotation_y)
        
        # return (self.pitch, self.roll, self.gyro_scaled_x, self.gyro_scaled_y, self.gyro_scaled_z, self.accel_scaled_x, self.accel_scaled_y, self.accel_scaled_z)
        return (self.pitch, self.roll, self.gyro_scaled_x, self.gyro_scaled_y, self.gyro_scaled_z, self.accel_scaled_x, self.accel_scaled_y, self.accel_scaled_z)
        
    def read_x_rotation(self, x, y, z):
        return (math.atan2(y, self.distance(x, z)))

    def read_y_rotation(self, x, y, z):
        return (-math.atan2(x, self.distance(y, z)))

    def distance(self, x, y):
        '''Returns the distance between two point in 2d space'''
        return math.sqrt((x * x) + (y * y))

    def comp_filter(self, current_x, current_y):
        new_pitch = IMU.K * (self.pitch + self.gyro_scaled_x * self.time_diff) + (IMU.K1 * current_x)
        new_roll = IMU.K * (self.roll + self.gyro_scaled_y * self.time_diff) + (IMU.K1 * current_y)
        return (new_pitch, new_roll)


    def read_pitch_roll_yaw(self):
        '''
        Return pitch, roll and yaw in radians
        '''
        (raw_pitch, raw_roll, self.gyro_scaled_x, self.gyro_scaled_y, \
            self.gyro_scaled_z, self.accel_scaled_x, self.accel_scaled_y, \
            self.accel_scaled_z) = self.read_all()
        
        now = time.time()
        self.time_diff = now - self.last_time
        self.last_time = now 
        
        (self.pitch, self.roll) = self.comp_filter(raw_pitch, raw_roll)
        self.yaw = self.read_compensated_bearing(self.pitch, self.roll)
        
        return (self.pitch, self.roll, self.yaw)

    def read_compensated_bearing(pitch,roll):
        '''
        Compensate bearing for pitch and roll
        '''
        x = self.accel_scaled_x
        z = self.accel_scaled_z

        cos_pitch = (math.cos(pitch))
        sin_pitch = (math.sin(pitch))
        
        cos_roll = (math.cos(roll))
        sin_roll = (math.sin(roll))
    
        Xh = (x * cos_roll) + (z * sin_roll)
        Yh = (x * sin_pitch * sin_roll) + (z * cos_pitch) - (z * sin_pitch * cos_roll)
        
        bearing = math.atan2(Yh, Xh)
        if bearing < 0:
            return bearing + self.TWO_PI
        else:
            return bearing
