#!/usr/bin/python3

import subprocess

subprocess.call('2d-calibration-get-samples')

subprocess.call('2d-calibration-make-calc magnet-data_20181018_1711.txt')
