#!/usr/bin/python3

import sys
sys.path.insert(0,'/home/pi/mpu6050')
from mpu6050 import mpu6050
from py_qmc5883l import QMC5883L
import ProcBigEasyDriver as pbed
import datetime as dt
import os
import threading
import csv
import time
import math
from get_data import IMU
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
import astropy.units as u
from astropy.time import Time

#Initiate global pos


lat = 53.21629287617459#TODO: Get GPS?
lon = 6.556274609173566

def data_daemon():
    """Daemon computing the position as perceived by sensor"""
    global pos
    #[pitch,roll,yaw] = [alt,roll,az] pos #TODO: See how well this works when all is aligned
    
    imu = IMU(lat,lon)
    next = dt.datetime.now()
    pos = imu.read_pitch_roll_yaw()
    while True:
        pos = imu.read_pitch_roll_yaw()

if __name__ == '__main__':
    print('Starrting daemon') #FIXME: Check coordinate systems used, values are wrong should be deg
    t=threading.Thread(group=None, target=data_daemon, daemon=True)
    t.start() #Figure out the below
    while True:
        time.sleep(1)
        print(pos)
        print([i*180/math.pi for i in pos])


class MountControl:
    """Class controling the telescope"""

    stepsize = 16#TODO:
    dec_rpm = 0.25/360

    lat = lat
    lon = lon
    
    def __init__(self, lat=None, lon=None) -> None:
        if lat!=None:
            self.lat=lat
        if lon!=None:
            self.lon=lon
        #Start thread for recording movement
        self.t = threading.Thread(group=None, target=data_daemon, daemon=True)
        self.t.start() #Figure out the below
        self.motor_alt = pbed.ProcBigEasyDriver(step, direction, ms1, ms2, ms3, enable, #TODO Add pins
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

        new = pos[1]+deg
        while pos[1]!=new:
            pass
        #Reset rpm
        self.motor_az.set_rpm(dec_rpm)
        
        return 0
    
    def go_to_object(self,obj):
        '''loads ra/dec from objects folder and moves telescope'''
        #Get ra/dec
        if obj[0] == 'M': file_name = os.path.join('./objects', 'MessierObjects.xls')
        if obj[0] == 'N': file_name = os.path.join('./objects', 'NGCObjects.xls')
        index = int(obj.split(' ')[-1])+1 #+1 since the file contains headers
        #Only load relevant row
        with open(file_name, "rt") as infile:
            r = csv.reader(infile)
            for i in range(index):
                next(r)     
            row = next(r)   
        ra = row[3:5]
        dec = row[5:8]
        del row, index, file_name
        #Get alt az
        (alt,az)=self.radec_altaz(ra,dec)
        #Move motors
        self.rotate_az(pos[0]-az)
        self.rotate_alt(pos[2]-alt)
        #Debugging until tracking accuracy is determined
        print('az offset: {}, alt offset: {}'.format(pos[0]-az,pos[2]-alt))
        return 0

    def radec_altaz(self,ra,dec):
        """Ra Dec to Alt Az"""
        #Get ra and dec as degrees
        ra = (ra[0]+ra[1]/60)*15
        dec = dec[1]+dec[2]
        if dec[0]=='-':
            dec = -dec
        #Set astropy variables
        l = EarthLocation(self.lon,self.lat,height=5*u.m) #change height somehow but shouldnt matter 
        obj = SkyCoord(ra*u.deg,dec*u.deg,frame='icrs')
        altaz = AltAzs(location=l,obstime=Time.now())
        obj.transform_to(altaz)
        (alt,az)=(obj.alt, obj.az)
        del obj, altaz, l
        return (alt,az)

    def stop(self):
        """Stops measurements and motors"""
        self.motor_alt.stop()
        self.motor_az.stop()
        self.t.stop()
        return 0

        

