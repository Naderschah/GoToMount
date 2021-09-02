#!/usr/bin/python3

import ProcBigEasyDriver as pbed
import datetime as dt
import os
import threading
import csv
import time
from get_data import IMU
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
import astropy.units as u
from astropy.time import Time

#Initiate global pos


class Data_Daemon:
    """Daemon computing the position as perceived by sensor"""
    pos = [0,0,0]
    def __init__(self) -> None:    
        pass
    
    @classmethod
    def get(cls):
        return cls.pos
    
    def run(self):
        imu = IMU(lat,lon)
        next = dt.datetime.now()
        pos = imu.read_pitch_roll_yaw()
        while True:
            pos = imu.read_pitch_roll_yaw()


class MountControl:
    """Class controling the telescope"""

    stepsize = 16
    dec_rpm = 0.25/360
    lat = 53.21629287617459 #TODO: GPS?
    lon = 6.556274609173566
    obj = None

    def __init__(self, lat=None, lon=None) -> None:
        if lat!=None:
            self.lat=lat
        if lon!=None:
            self.lon=lon
        #Start thread for recording movement
        self.t = threading.Thread(group=None, target=Data_Daemon, daemon=True)
        #self.t.start() #Figure out the below
        self.motor_alt = pbed.ProcBigEasyDriver(step=13, direction=19, ms1=21, ms2=20, ms3=16, enable=26,
                                   microstepping=self.stepsize, rpm=self.dec_rpm, steps_per_rev=200*self.stepsize,
                                   Kp=0.2, Ki=0.1) #What is Kp and Ki
        self.motor_alt.enable()
        self.motor_az = pbed.ProcBigEasyDriver(step=27, direction=17, ms1=23, ms2=24, ms3=25, enable=12, 
                                   microstepping=self.stepsize, rpm=self.dec_rpm, steps_per_rev=200*self.stepsize,
                                   Kp=0.2, Ki=0.1)
        self.motor_az.enable()

    def correct(self, alt, az):
        """Make correction to current coordinates"""
        rpm = 5
        dpm = rpm*360
        
        #Save current position
        coord = self.t.get()
        #Time based indexing of rotation
        sec_for_rot = (az/dpm)*60
        t = dt.datetime.now()+dt.timedelta(seconds=sec_for_rot)
        self.motor_az.set_rpm(rpm)
        while dt.datetime.now() > t:
            pass
        self.motor_az.set_rpm(self.dec_rpm)
        #Time based indexing of rotation
        sec_for_rot = (alt/dpm)*60
        t = dt.datetime.now()+dt.timedelta(seconds=sec_for_rot)
        self.motor_alt.set_rpm(rpm)
        while dt.datetime.now() > t:
            pass
        self.motor_alt.set_rpm(self.dec_rpm)
        #Set global pos
        self.t.pos = coord
        return 0

    def rotate_az(self,az):
        """Rotate Motor1 Az"""
        #Change motor speed
        self.motor_az.set_rpm(5)

        if az < self.t.get()[0]:
            self.motor_az.reverse()
            rev = True
        else:
            rev =False

        while self.t.get()[0]!=az:
            pass
        #Reset rpm
        self.motor_az.set_rpm(self.dec_rpm)

        return 0

    def rotate_alt(self,alt):
        """Rotate Motor2 Alt
        -------------------------
        gets global pos for positional data as returned by data_daemon
        Modify coefficients!
        """

        #Change motor speed
        self.motor_alt.set_rpm(5)

        if alt < self.t.get()[0]:
            self.motor_alt.reverse()
            rev = True
        else:
            rev =False

        while self.t.get()[1]!=alt:
            pass

        #Reset rpm
        self.motor_alt.set_rpm(self.dec_rpm)
        if rev:
            self.motor_alt.forwards()
        
        return 0
    
    def go_to_object(self,obj):
        '''loads ra/dec from objects folder and moves telescope'''
        #Get ra/dec
        self.obj = obj
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
        self.rotate_az(az)
        self.rotate_alt(alt)
        #Debugging until tracking accuracy is determined
        print('az offset: {}, alt offset: {}'.format(self.t.get()[0]-az,self.t.get()[2]-alt))
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
        altaz = AltAz(location=l,obstime=Time.now())
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

        
if __name__ == '__main__':
    print('Starting daemon')
    #mount = MountControl()
    t=threading.Thread(group=None, target=data_daemon, daemon=True)
    t.start() #Figure out the below
    while True:
        time.sleep(1)
        print(t.get())
