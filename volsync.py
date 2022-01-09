#!/usr/bin/python3
# -*- coding: utf-8 -*-

import _thread
import alsaaudio
import time
import spidev
import select

mixer_name = 'Master'

#------------------------------------------------------------------------------#
#      initialize some things at the beginning and set initial volume          #
#------------------------------------------------------------------------------#
def init():
    global spi
    global mixer
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 976000
    mixer = alsaaudio.Mixer(mixer_name)
    alsa_val = mixer.getvolume()
    volume = alsa_val[0]
    set_potentiometer(volume)

#------------------------------------------------------------------------------#
#                       watch volume changes                                   #
#------------------------------------------------------------------------------#
def volume_watch():
    global volume
    poll = select.poll()
    descriptors = mixer.polldescriptors()
    poll.register(descriptors[0][0])
    print('starting monitor for alsa volume ...')
    while True:
        events = poll.poll()
        mixer.handleevents()
        for e in events:
            alsa_val = mixer.getvolume()
            volume = alsa_val[0]
            set_potentiometer(volume)

#------------------------------------------------------------------------------#
#                start thread for watching volume change                       #
#------------------------------------------------------------------------------#
def run_control_watch():
    try:
        _thread.start_new_thread( volume_watch, () )
    except:
        print("Error: unable to start thread volume_watch")
        exit(1)

#------------------------------------------------------------------------------#
#                   set potentiometer MCP4151                                  #
#------------------------------------------------------------------------------#
def set_potentiometer(value):
    scaled_value = 255-int(2.55*value)
    msb = scaled_value >> 8
    lsb = scaled_value & 0xFF
    spi.xfer([msb, lsb])

#------------------------------------------------------------------------------#
#                   main programm                                              #
#------------------------------------------------------------------------------#
init()
run_control_watch()
while True:
    time.sleep(100)
