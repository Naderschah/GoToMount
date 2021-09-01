## Modfied: https://github.com/bitify/raspi/blob/2619da30ec36b29e47baae9a65b89d19653b5ec2/i2c-sensors/bitify/python/sensors/imu.py
# and https://github.com/bitify/raspi/blob/2619da30ec36b29e47baae9a65b89d19653b5ec2/i2c-sensors/bitify/python/sensors/mpu6050.py
# and https://github.com/RigacciOrg/py-qmc5883l/blob/master/py_qmc5883l/__init__.py
# and https://github.com/bitify/raspi/blob/master/i2c-sensors/bitify/python/utils/i2cutils.py


import time
from py_qmc5883l import QMC5883L
import geomag
import math
import smbus

def return_list(dict):
    x = dict['x']
    y = dict['y']
    z = dict['z']
    return [x,y,z]

class IMU(object):
    
    K = 0.98
    K1 = 1 - K
    TWO_PI = (2*math.pi)
    
    def __init__(self, lat, lon):

        self.gyroscope = MPU6050(smbus.SMBus(1), 0x68, 'gyroscope', fs_scale=MPU6050.FS_2000, afs_scale=MPU6050.AFS_16g)
        self.compass = QMC5883L()
        self.compass.declination = geomag.declination(lat,lon)

        self.last_time = time.time()
        self.time_diff = 0

        # Take a reading as a starting point
        (self.pitch, self.roll, self.gyro_scaled_x, self.gyro_scaled_y, \
            self.gyro_scaled_z, self.accel_scaled_x, self.accel_scaled_y, \
            self.accel_scaled_z) = self.gyroscope.read_all()
        
        
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
        
        return [self.pitch, self.roll, self.yaw]

    def read_compensated_bearing(self,pitch,roll):
        '''
        Compensate bearing for pitch and roll
        '''
        [x, y, z, t] = self.compass.get_data()
        #Calibrate x and z
        c = self.compass._calibration
        x = x * c[0][0] + y * c[0][1] + c[0][2]
        z = x * c[2][0] + y * c[2][1] + c[2][2]

        cos_pitch = (math.cos(pitch))
        sin_pitch = (math.sin(pitch))
        
        cos_roll = (math.cos(roll))
        sin_roll = (math.sin(roll))
    
        Xh = (x * cos_roll) + (z * sin_roll)
        Yh = (x * sin_pitch * sin_roll) + (z * cos_pitch) - (z * sin_pitch * cos_roll)
        
        bearing = math.atan2(Yh, Xh)
        if bearing < 0:
            return bearing + self.TWO_PI + self.compass._declination
        else:
            return bearing+self.compass._declination




#https://github.com/bitify/raspi/blob/2619da30ec36b29e47baae9a65b89d19653b5ec2/i2c-sensors/bitify/python/sensors/mpu6050.py
class MPU6050(object):
    '''
    Simple MPU-6050 implementation
    '''

    PWR_MGMT_1 = 0x6b

    FS_SEL = 0x1b
    FS_250 = 0
    FS_500 = 1
    FS_1000 = 2
    FS_2000 = 3

    AFS_SEL = 0x1c
    AFS_2g = 0
    AFS_4g = 1
    AFS_8g = 2
    AFS_16g = 3

    ACCEL_START_BLOCK = 0x3b
    ACCEL_XOUT_H = 0
    ACCEL_XOUT_L = 1
    ACCEL_YOUT_H = 2
    ACCEL_YOUT_L = 3
    ACCEL_ZOUT_H = 4
    ACCEL_ZOUT_L = 5

    ACCEL_SCALE = { AFS_2g  : [ 2, 16384.0], AFS_4g  : [ 4, 8192.0], AFS_8g  : [ 8, 4096.0], AFS_16g : [16, 2048.0] }

    TEMP_START_BLOCK = 0x41
    TEMP_OUT_H = 0
    TEMP_OUT_L = 1

    GYRO_START_BLOCK = 0x43
    GYRO_XOUT_H = 0
    GYRO_XOUT_L = 1
    GYRO_YOUT_H = 2
    GYRO_YOUT_L = 3
    GYRO_ZOUT_H = 4
    GYRO_ZOUT_L = 5

    GYRO_SCALE = { FS_250  : [ 250, 131.0], FS_500  : [ 500, 65.5], FS_1000 : [1000, 32.8], FS_2000 : [2000, 16.4] }

    K = 0.98
    K1 = 1 - K

    def __init__(self, bus, address, name, fs_scale=FS_250, afs_scale=AFS_2g):
        '''
        Constructor
        '''

        self.bus = bus
        self.address = address
        self.name = name
        self.fs_scale = fs_scale
        self.afs_scale = afs_scale
        
        self.raw_gyro_data = [0, 0, 0, 0, 0, 0]
        self.raw_accel_data = [0, 0, 0, 0, 0, 0]
        self.raw_temp_data = [0, 0]
        
        self.gyro_raw_x = 0
        self.gyro_raw_y = 0
        self.gyro_raw_z = 0
        
        self.gyro_scaled_x = 0
        self.gyro_scaled_y = 0
        self.gyro_scaled_z = 0
        
        self.raw_temp = 0
        self.scaled_temp = 0
        
        self.accel_raw_x = 0
        self.accel_raw_y = 0
        self.accel_raw_z = 0
        
        self.accel_scaled_x = 0
        self.accel_scaled_y = 0
        self.accel_scaled_z = 0
        
        self.pitch = 0.0
        self.roll = 0.0
        
        # We need to wake up the module as it start in sleep mode
        i2c_write_byte(self.bus, self.address, MPU6050.PWR_MGMT_1, 0)
        # Set the gryo resolution
        i2c_write_byte(self.bus, self.address, MPU6050.FS_SEL, self.fs_scale << 3)
        # Set the accelerometer resolution
        i2c_write_byte(self.bus, self.address, MPU6050.AFS_SEL, self.afs_scale << 3)
           
    def read_raw_data(self):
        '''
        Read the raw data from the sensor, scale it appropriately and store for later use
        '''
        self.raw_gyro_data = i2c_read_block(self.bus, self.address, MPU6050.GYRO_START_BLOCK, 6)
        self.raw_accel_data = i2c_read_block(self.bus, self.address, MPU6050.ACCEL_START_BLOCK, 6)
        self.raw_temp_data = i2c_read_block(self.bus, self.address, MPU6050.TEMP_START_BLOCK, 2)
        
        self.gyro_raw_x = twos_compliment(self.raw_gyro_data[MPU6050.GYRO_XOUT_H], self.raw_gyro_data[MPU6050.GYRO_XOUT_L])
        self.gyro_raw_y = twos_compliment(self.raw_gyro_data[MPU6050.GYRO_YOUT_H], self.raw_gyro_data[MPU6050.GYRO_YOUT_L])
        self.gyro_raw_z = twos_compliment(self.raw_gyro_data[MPU6050.GYRO_ZOUT_H], self.raw_gyro_data[MPU6050.GYRO_ZOUT_L])
        
        self.accel_raw_x = twos_compliment(self.raw_accel_data[MPU6050.ACCEL_XOUT_H], self.raw_accel_data[MPU6050.ACCEL_XOUT_L])
        self.accel_raw_y = twos_compliment(self.raw_accel_data[MPU6050.ACCEL_YOUT_H], self.raw_accel_data[MPU6050.ACCEL_YOUT_L])
        self.accel_raw_z = twos_compliment(self.raw_accel_data[MPU6050.ACCEL_ZOUT_H], self.raw_accel_data[MPU6050.ACCEL_ZOUT_L])
        
        self.raw_temp = twos_compliment(self.raw_temp_data[MPU6050.TEMP_OUT_H], self.raw_temp_data[MPU6050.TEMP_OUT_L])

        # We convert these to radians for consistency and so we can easily combine later in the filter
        self.gyro_scaled_x = math.radians(self.gyro_raw_x / MPU6050.GYRO_SCALE[self.fs_scale][1]) 
        self.gyro_scaled_y = math.radians(self.gyro_raw_y / MPU6050.GYRO_SCALE[self.fs_scale][1]) 
        self.gyro_scaled_z = math.radians(self.gyro_raw_z / MPU6050.GYRO_SCALE[self.fs_scale][1]) 

        self.scaled_temp = self.raw_temp / 340 + 36.53

        self.accel_scaled_x = self.accel_raw_x / MPU6050.ACCEL_SCALE[self.afs_scale][1]
        self.accel_scaled_y = self.accel_raw_y / MPU6050.ACCEL_SCALE[self.afs_scale][1]
        self.accel_scaled_z = self.accel_raw_z / MPU6050.ACCEL_SCALE[self.afs_scale][1]
        
        self.pitch = self.read_x_rotation(self.read_scaled_accel_x(),self.read_scaled_accel_y(),self.read_scaled_accel_z())
        self.roll =  self.read_y_rotation(self.read_scaled_accel_x(),self.read_scaled_accel_y(),self.read_scaled_accel_z())
        
    def distance(self, x, y):
        '''Returns the distance between two point in 2d space'''
        return math.sqrt((x * x) + (y * y))
    
    def read_x_rotation(self, x, y, z):
        '''Returns the rotation around the X axis in radians'''
        return math.atan2(y, self.distance(x, z))
    
    def read_y_rotation(self, x, y, z):
        '''Returns the rotation around the Y axis in radians'''
        return -math.atan2(x, self.distance(y, z))
    
    def read_raw_accel_x(self):
        '''Return the RAW X accelerometer value'''
        return self.accel_raw_x
        
    def read_raw_accel_y(self):
        '''Return the RAW Y accelerometer value'''
        return self.accel_raw_y
        
    def read_raw_accel_z(self):
        '''Return the RAW Z accelerometer value'''        
        return self.accel_raw_z
    
    def read_scaled_accel_x(self):
        '''Return the SCALED X accelerometer value'''
        return self.accel_scaled_x
    
    def read_scaled_accel_y(self):
        '''Return the SCALED Y accelerometer value'''
        return self.accel_scaled_y

    def read_scaled_accel_z(self):
        '''Return the SCALED Z accelerometer value'''
        return self.accel_scaled_z

    def read_raw_gyro_x(self):
        '''Return the RAW X gyro value'''
        return self.gyro_raw_x
        
    def read_raw_gyro_y(self):
        '''Return the RAW Y gyro value'''
        return self.gyro_raw_y
        
    def read_raw_gyro_z(self):
        '''Return the RAW Z gyro value'''
        return self.gyro_raw_z
    
    def read_scaled_gyro_x(self):
        '''Return the SCALED X gyro value in radians/second'''
        return self.gyro_scaled_x

    def read_scaled_gyro_y(self):
        '''Return the SCALED Y gyro value in radians/second'''
        return self.gyro_scaled_y

    def read_scaled_gyro_z(self):
        '''Return the SCALED Z gyro value in radians/second'''
        return self.gyro_scaled_z

    def read_temp(self):
        '''Return the temperature'''
        return self.scaled_temp
    
    def read_pitch(self):
        '''Return the current pitch value in radians'''
        return self.pitch

    def read_roll(self):
        '''Return the current roll value in radians'''
        return self.roll
        
    def read_all(self):
        '''Return pitch and roll in radians and the scaled x, y & z values from the gyroscope and accelerometer'''
        self.read_raw_data()
        return (self.pitch, self.roll, self.gyro_scaled_x, self.gyro_scaled_y, self.gyro_scaled_z, self.accel_scaled_x, self.accel_scaled_y, self.accel_scaled_z)








### I2Utils module from bitify raspi
def i2c_raspberry_pi_bus_number():
    """Returns Raspberry Pi I2C bus number (integer, 0 or 1).
    Looks at `/proc/cpuinfo` to identify if this is a revised model
    of the Raspberry Pi (with 512MB of RAM) using `/dev/i2c-1`, or
    the original version (with 256MB or RAM) using `/dev/i2c-0`.
    """
    return 1 
    
def i2c_read_byte(bus, address, register):
    return bus.read_byte_data(address, register)
 
def i2c_read_word_unsigned(bus, address, register):
    high = bus.read_byte_data(address, register)
    low = bus.read_byte_data(address, register+1)
    return (high << 8) + low

def i2c_read_word_signed(bus, address, register):
    value = i2c_read_word_unsigned(bus, address, register)
    if (value >= 0x8000):
        return -((0xffff - value) + 1)
    else:
        return value

def i2c_write_byte(bus, address, register, value):
    bus.write_byte_data(address, register, value)

def i2c_read_block(bus, address, start, length):
    return bus.read_i2c_block_data(address, start, length)

def twos_compliment(high_byte, low_byte):
    value = (high_byte << 8) + low_byte
    if (value >= 0x8000):
        return -((0xffff - value) + 1)
    else:
        return value