import subprocess

subprocess.call('/home/pi/py-qmc5883L/calibration/2d-calibration-get-samples')

subprocess.call('2d-calibration-make-calc magnet-data_20181018_1711.txt > gnuplot-script')
