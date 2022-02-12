import gpiozero
from time import sleep
import datetime as dt


pbed.ProcBigEasyDriver(step=13, direction=19, ms1=21, ms2=20, ms3=16, enable=26,
                                   microstepping=self.stepsize, rpm=self.dec_rpm, steps_per_rev=200*self.stepsize,
                                   Kp=0.2, Ki=0.1) #What is Kp and Ki

(step, direction, ms1, ms2, ms3, enable, microstepping, rpm, steps_per_rev) = (13, 19, 21, 20, 16, 26, 1, 1, 200)

pin_dir = gpiozero.LED(direction)

pin_ms1 = gpiozero.LED(ms1)

pin_ms2 = gpiozero.LED(ms2)

pin_ms3 = gpiozero.LED(ms3)

pin_en = gpiozero.LED(enable)

pin_step = gpiozero.LED(step)

#Set microstepping to 1
pin_ms1.off()
pin_ms2.off()
pin_ms3.off()

#Enable motor
pin_en.on()
#Set direction
pin_dir.off()
i=0
while i < 50:
    i += 1
    pin_step.on()
    sleep(2)
    pin_step.off()
    sleep(2)