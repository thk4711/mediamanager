#!/usr/bin/python3

import RPi.GPIO as GPIO
import sys
import alsaaudio
import time
out_device      = None

#------------------------------------------------------------------------------#
#                    do some stuff at the beginning                            #
#------------------------------------------------------------------------------#
def init():
    global modes
    global open_audio_device
    global hardware
    hardware = {}
    hardware['GPIO'] = {'I2S switch pin 1': 4, 'I2S switch pin 2': 17}
    hardware['I2C'] = {'PCM5122 controls': 0x4d}
    hardware['mixer'] = 'Digital'

    modes = {'default': { 4: False, 17: False },
             'usb':     { 4: True,  17: False },
	         'aux':     { 4: True,  17: True }}

    open_audio_device = {'default': False, 'aux': True }
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(hardware['GPIO']['I2S switch pin 1'], GPIO.OUT)
    GPIO.setup(hardware['GPIO']['I2S switch pin 2'], GPIO.OUT)

#------------------------------------------------------------------------------#
#                return hardware information                                   #
#------------------------------------------------------------------------------#
def hwinfo():
    return(hardware)

#------------------------------------------------------------------------------#
#                this is called if mode is switched                            #
#------------------------------------------------------------------------------#
def switch_mode(mode):
    handle_gpios(mode)
    handle_audio_device(mode)

#------------------------------------------------------------------------------#
#                    switch gpio's as needed                                   #
#------------------------------------------------------------------------------#
def handle_gpios(mode):
    if mode not in modes:
        mode = 'default'
    for io in modes[mode]:
        GPIO.output(io, modes[mode][io])

#------------------------------------------------------------------------------#
#          open audio device to prevent the DAC from muting                    #
#------------------------------------------------------------------------------#
def handle_audio_device(mode):
    global out_device
    if mode not in modes:
        mode = 'default'
    if open_audio_device[mode]:
        time.sleep(1)
        try:
            out_device = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, device='hw:0,0')
        except:
            print('failed to open audio device')
        return
    try:
        out_device.close()
    except:
        pass
