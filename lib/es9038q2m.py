#!/usr/bin/python3

import RPi.GPIO as GPIO
import sys

def init():
    global modes
    modes = {'default': { 4:False, 17:False, 22:False, 27:False },
             'coax':    { 4:False, 17:False, 22:False, 27:True },
             'toslink': { 4:False, 17:False, 22:True, 27:False },
             'usb':     { 4:True, 17:False, 22:False, 27:False },
	         'aux':     { 4:True, 17:True, 22:False, 27:False }
	         }

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4, GPIO.OUT)
    GPIO.setup(17, GPIO.OUT)
    GPIO.setup(22, GPIO.OUT)
    GPIO.setup(27, GPIO.OUT)

def switch_mode(mode):
    if mode not in modes:
        mode = 'default'
    for io in modes[mode]:
        set_io(io,modes[mode][io])

def set_io(io,state):
    print('setting',io,'to',state)
    GPIO.output(io, state)

#init()
#mode = sys.argv[1]
#switch_mode(mode)
