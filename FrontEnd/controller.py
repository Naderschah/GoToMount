import os
import termios
import sys, tty
import time
import datetime as dt

from ..camera_control import Camera_control
from test import MountControl
#Change dir to current scripts
os.chdir(os.path.dirname(__file__))

def clear_lines():
    """Clear earlier printed"""
    os.system('cls' if os.name == 'nt' else "printf '\033c'")

def usr_in(string):
    """1 character user input doesnt wait for \n"""
    print(string)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        clear_lines()
    return ch

def delete_last_line():
    "Use this function to delete the last line in the STDOUT"

    #cursor up one line
    sys.stdout.write('\x1b[1A')

    #delete last line
    sys.stdout.write('\x1b[2K')


def load_calibration(file_path):
    """Loads calibration file"""
    cal = open(file_path)
    cont = cal.read().split(',')
    cal.close()
    print('Loading Calibration not Implemented yet')
    #TODO:

def calibrate():
    from ..calibration.calibration_get_samples import main
    main()
    del main
    from ..calibration.calibration_make_calc import main
    main() #TODO: Add flags for filepaths
    del main
    file_path = ''
    load_calibration(file_path)

def measure_noise():
    """Get test settings that dont change to frequently"""
    #https://www.cloudynights.com/articles/cat/column/fishing-for-photons/signal-to-noise-part-3-measuring-your-camera-r1929
    print('We must first take several calibration frames, cover the camera to take the dark frames')
    var = input('When ready press enter to continue, the next step will take a bit over 30 minutes')
    cc = Camera_control() #FIXME: Set BULB exposure
    #take darks
    cc.set_config(exp=60,iso=800) 
    im_folder = '/home/pi/{}_{}'.format('dark_1m', dt.datetime.now().strftime('%Y%m%d'))
    for i in range(60):
        cc.make_image(im_folder)
    if not os.path.isdir(im_folder):
        os.mkdir(im_folder)
    var = input('Now we will take 250 bias frames, keep the camera covered (also the viewfinder), press enter when ready')
    #take bias
    cc.set_config(exp=1/4000,iso=800) 
    im_folder = '/home/pi/{}_{}'.format('bias', dt.datetime.now().strftime('%Y%m%d'))
    if not os.path.isdir(im_folder):
        os.mkdir(im_folder)
    for i in range(250):
        cc.make_image(im_folder)
    var = input('We will now make another set of dark frames but with varying length')
    #take varying dark
    im_folder = '/home/pi/{}_{}'.format('dark_range', dt.datetime.now().strftime('%Y%m%d'))
    if not os.path.isdir(im_folder):
        os.mkdir(im_folder)
    for i in (1,2,5,10):
        cc.set_config(exp=i*60,iso=800)
        cc.make_image(im_folder)
    var = input('Now we need to take flats, use 6 sheets of standard paper as a diffuser and aim the lens at a white wall')
    im_folder = '/home/pi/{}_{}'.format('flats', dt.datetime.now().strftime('%Y%m%d'))
    if not os.path.isdir(im_folder):
        os.mkdir(im_folder)
    for i in (6,5,4,3,2,1):
        var = input('We will now take the image with {} papers'.format(i))
        cc.set_config(exp=1/10,iso=800)
        cc.make_image(im_folder)
        cc.make_image(im_folder)
    print('The image collection procedure is completed')
    #FIXME: Add computation of images https://www.cloudynights.com/articles/cat/column/fishing-for-photons/signal-to-noise-part-3-measuring-your-camera-r1929
        


def get_exp_iso():
    """Get best exposure and iso for object""" 
    #First Get all the data
    iso = 800 #https://dslr-astrophotography.com/iso-values-canon-cameras/
    if not os.path.isfile('../calibration/camera_measurements'):
        print('There is no configuration file')
        time.sleep(5)
        return None, None, None
    f = open('../calibration/camera_measurements','r')
    cont = f.read()
    f.close()
    import json
    cont = json.loads(cont)
    #Now do the math, taken from http://www.gibastrosoc.org/sections/astrophotography/optimum-exposures-calculator
    #General properties #TODO MAny of these properties will be established on site with a test image: IMPLEMENT
    if cont['Full Well Capacity']/cont['Gain']*0.7>65535: flat_cal_max = 65535
    else: flat_cal_max =cont['Full Well Capacity']/cont['Gain']*0.7>65535
    
    background_flux = cont['Median Background Flux']*cont['Gain']/cont['Exposure Time']
    full_well_capacity = cont['Full Well Capcity']/((cont['Bright Area of Interest Maximum']*cont['Gain'])/cont['Exposure Time'])
    
    SNR_perc = 0.95 #Percentage of ideal signal to noise ratio to achieve

    exp = (SNR_perc**2)*(cont['Readout Noise']**2)/((cont['Dark Current Noise']+background_flux)*(1-SNR_perc**2))

    desired_boost_ksc = 2 #Desired SNR boost through kappa sigma clipping

    rep = (desired_boost_ksc/0.8)**(1/0.28)
    #Round up
    if rep == int(rep): rep = int(rep)
    else: rep = int(rep)+1

    return exp, iso,rep
    


if __name__=='__main__':
    var = usr_in('Would you like to pick an old calibration (o) or recalibrate (r)? ')
    if var == 'o':
        while True:
            print('Which file should be loaded?')
            files = os.listdir('../calibration_files')
            for i,j in enumerate():
                print('{}) {}'.format(i,j))
            var = usr_in()
            try: 
                var = int(var)
                break
            except:
                print('A number is required') 
    
        load_calibration(os.path.join('../calibration_files',files[var]))
        del var, files
    else:
        calibrate()

    print('Starting sensors and telescope')

    mc = MountControl()
    
    clear_lines()

    while True:
        print('Telescope Operational\n')

        print('Current orientation: az={} alt={}'.format(*mc.t.get()[0:2:2]))

        choice = usr_in('q) stop; g) go to object; c) make alignment correction d) Imaging routine e) create camera measurements')

        if choice == 'q':
            mc.stop()
            break

        if choice == 'g':
            clear_lines()
            obj = input('Enter NGC or M catalogue name')
            mc.go_to_object(obj)
            clear_lines()
            del obj
        
        if choice == 'c':
            [alt,az] = input('Enter the degrees to move in alt and az comma seperated').split(',')
            mc.correct(alt,az)
            clear_lines()
            del alt, az

        if choice == 'd':
            cc = Camera_control()
            clear_lines()
            cc.get_config()
            #Get imaging parameters
            
            while True:
                choice = usr_in('s) select parameters a) automatically calculate parameters for current object')
                if choice == 's':
                    iso, exp = input('Enter iso and exposure comma seperated ').split(',')
                    try: 
                        iso = int(iso)
                        exp = exp.split('/')
                        if len(exp)==1: exp=float(exp[0])
                        else: exp = float(exp[0])/float(exp[1])
                    except:
                        print('Invalid parameters, try again')
                        pass
                    clear_lines()
                    if exp < 0.3:
                        print('iso: {} , exp: 1/{}'.format(iso, 1/exp))
                    else:
                        print('iso: {} , exp: {}'.format(iso, exp))
                    try:
                        rep = input('How many images should be taken? ')
                        rep = int(rep)
                    except:
                        print('Invalid parameter try again')
                    break

                if choice == 'a':
                    #print('Getting best parameters')
                    exp,iso,rep = get_exp_iso()
                    if exp == None: break
                    cc.set_config(exp,iso)
                    clear_lines()
                    cc.get_config(out=False)
                    yn = input('Are {} images doable? (y/n) '.format(rep))
                    if yn.upper() != 'Y':
                        rep = input('How many images should be taken? ')
                        rep = int(rep)
                    del yn
            if exp == None: break
            cc.set_config(exp,iso)
            clear_lines()
            cc.get_config(out=False)       

            print('Imaging will be completed in {} minutes'.format(exp*rep/60))
            del exp, iso
            im_folder = '/home/pi/{}_{}'.format(mc.obj.strip(' '), dt.datetime.now().strftime('%Y%m%d'))
            if not os.path.isdir(im_folder):
                os.mkdir(im_folder)
            print('All images will be stored in {}'.format(im_folder))
            for i in range(rep):
                cc.make_image(im_folder)
                print('Image {} completed'.format(i)) #TODO: Figure out Bias Dark and Flat
            clear_lines()
            print('Imaging of {} completed with {} images'.format(mc.obj, i+1))
            cc.close()
            del cc, im_folder

        if choice == 'e':
            measure_noise()



