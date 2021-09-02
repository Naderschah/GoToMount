#!/usr/bin/python3

from typing import OrderedDict, ValuesView
import gphoto2 as gp
import time
import os


class Camera_control:
    def __init__(self) -> None:
        self.camera = gp.Camera()
        print('Please connect and switch on your camera')
        while True:
            try:
                self.camera.init()
            except gp.GPhoto2Error as ex:
                if ex.code == gp.GP_ERROR_MODEL_NOT_FOUND:
                    # no camera, try again in 2 seconds
                    time.sleep(2)
                    continue
                # some other error we can't handle here
                raise
            # operation completed successfully so exit loop
            break

    def make_image(self, im_folder):
        file_path = cc.camera.capture(gp.GP_CAPTURE_IMAGE)
        target = os.path.join(im_folder,file_path.name)
        camera_file = self.camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        print(target)
        camera_file.save(target)

    def get_config(self,out=True):
        """Get current camera configuration"""
        conf = self.camera.get_config()
        iso = conf.get_child_by_name('iso').get_value()
        exp = conf.get_child_by_name('shutterspeed').get_value()
        print('iso = {}, exposure = {}'.format(iso,exp))
        if out:
            print('Choices for iso are: 100,200,400,800,1600,3200,6400')
            print('Choices for exposure are: 30,25,20,15,13,10.3,8,6.3,5,4,3.2,2.5,2,1.6,1.3,1,0.8,0.6,0.5,0.4,0.3,1/4,1/5,1/6,1/8,1/10,1/13,1/15,1/20,1/25,1/30,1/40,1/50,1/60,1/80,1/100,1/125,1/160,1/200,1/250,1/320,1/400,1/500,1/640,1/800,1/1000,1/1250,1/1600,1/2000,1/2500,1/3200,1/4000')

    def set_config(self, exposure, iso):
        """Change imaging parameters (iso+exposure)
        Requires that the index of choice is given
        """
        conf = self.camera.get_config()
        
        isoc = conf.get_child_by_name('iso')
        iso_ls = [100,200,400,800,1600,3200,6400]
        val = isoc.get_choice(iso_ls.index(iso)+1) #+1 because of different indexing
        isoc.set_value(val)

        expc = conf.get_child_by_name('shutterspeed') #FIXME: Set Bulb exposure somehow
        exp_ls = [30,25,20,15,13,10.3,8,6.3,5,4,3.2,2.5,2,1.6,1.3,1,0.8,0.6,0.5,0.4,0.3,1/4,1/5,1/6,1/8,1/10,1/13,1/15,1/20,1/25,1/30,1/40,1/50,1/60,1/80,1/100,1/125,1/160,1/200,1/250,1/320,1/400,1/500,1/640,1/800,1/1000,1/1250,1/1600,1/2000,1/2500,1/3200,1/4000]
        exp_ls = [float(i) for i in exp_ls]
        val = expc.get_choice(exp_ls.index(exposure)+1)
        expc.set_value(val)

        self.camera.set_config(conf)

    def close(self):
        self.camera.exit()




'''
The below is to print all choices


def get_gphoto2_CameraWidgetType_string(innumenum):
    switcher = {
        0: "GP_WIDGET_WINDOW",
        1: "GP_WIDGET_SECTION",
        2: "GP_WIDGET_TEXT",
        3: "GP_WIDGET_RANGE",
        4: "GP_WIDGET_TOGGLE",
        5: "GP_WIDGET_RADIO",
        6: "GP_WIDGET_MENU",
        7: "GP_WIDGET_BUTTON",
        8: "GP_WIDGET_DATE"
    }
    return switcher.get(innumenum, "Invalid camwidget type")

def get_camera_config_children(childrenarr, savearr):
    for child in childrenarr:
        tmpdict = OrderedDict()
        tmpdict['ro'] = child.get_readonly()
        tmpdict['name'] = child.get_name()
        tmpdict['label'] = child.get_label()
        tmpdict['type'] = child.get_type()
        tmpdict['typestr'] = get_gphoto2_CameraWidgetType_string( tmpdict['type'] )
        if ((tmpdict['type'] == gp.GP_WIDGET_RADIO) or (tmpdict['type'] == gp.GP_WIDGET_MENU)):
            tmpdict['count_choices'] = child.count_choices()
            tmpchoices = []
            for choice in child.get_choices():
                tmpchoices.append(choice)
            tmpdict['choices'] = ",".join(tmpchoices)
        if (child.count_children() > 0):
            tmpdict['children'] = []
            get_camera_config_children(child.get_children(), tmpdict['children'])
        else:
            # NOTE: camera HAS to be "into preview mode to raise mirror", otherwise at this point can get "gphoto2.GPhoto2Error: [-2] Bad parameters" for get_value
            try:
                tmpdict['value'] = child.get_value()
            except Exception as ex:
                tmpdict['value'] = "{} {}".format( type(ex).__name__, ex.args)
        savearr.append(tmpdict)


arr = []
get_camera_config_children(conf.get_children(), arr)

for i in arr:
    print(i)
'''
cc.close()