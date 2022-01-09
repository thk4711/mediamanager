#!/usr/bin/python3
# -*- coding: utf-8 -*-

import _thread
import alsaaudio
import time
import argparse
import alsaaudio
import pathlib
import select
import lib.common as common
from evdev import InputDevice, categorize, ecodes, list_devices

#-----------------------------------------------------------------#
#             do some things at the beginning                     #
#-----------------------------------------------------------------#
def init():
    global mixer
    global lirc_device
    global volume
    global old_volume
    global host
    global port
    global config
    parser = argparse.ArgumentParser(description='media helper')
    parser.add_argument('-p', '--port', type=int, help='manager port', required=True)
    parser.add_argument('-ho', '--host', type=str, help='manager host', required=False, default='localhost')
    parser.add_argument('-m', '--mixer', type=str, help='volume mixer name', required=False, default='Master')
    args = parser.parse_args()
    port = args.port
    host = args.host
    mixer_name = args.mixer
    mixer = alsaaudio.Mixer(mixer_name)
    alsa_val = mixer.getvolume()
    value = alsa_val[0]
    volume = value
    old_volume = -1
    devices = [InputDevice(path) for path in list_devices()]
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/infrared.conf')
    for device in devices:
        if device.name == config['general']['device-name']:
            lirc_device = InputDevice(device.path)
            print('device',lirc_device)

#-----------------------------------------------------------------#
#             translate key code to string                        #
#-----------------------------------------------------------------#
def key_code_to_action(code):
    print(code)
    action = config['buttons'][str(code)]
    print(action)
    if action == 'volume+' : volume_adjust(1)
    elif action == 'volume-' : volume_adjust(-1)
    elif 'station' in action:
        action = action.replace('station=','')
        common.get_data(host,port,'switchservice/service=Radio')
        common.get_data(host,port,'playindex/index=' + action)
    else:
        common.get_data(host,port,action)

#-----------------------------------------------------------------#
#             adjust volume                                       #
#-----------------------------------------------------------------#
def volume_adjust(diff):
    global volume
    volume = volume + diff
    if volume > 100:
        volume = 100
    if volume < 0:
        volume = 0
    mixer.setvolume(volume)

#-----------------------------------------------------------------#
#                 background thred to get keycode                 #
#-----------------------------------------------------------------#
def run_ir_monitor(lirc_device):
    repeat_cout = 0
    for event in lirc_device.read_loop():
        if event.type == ecodes.EV_KEY:
            if event.value == 1:
                key_code_to_action(event.code)
            elif event.value == 2:
                repeat_cout = repeat_cout +1
                if repeat_cout > 4:
                    key_code_to_action(event.code)
            elif event.value == 0:
                repeat_cout = 0

#------------------------------------------------------------------------------#
#           start thread ifrared monitor                                       #
#------------------------------------------------------------------------------#
def ir_monitor():
    try:
        _thread.start_new_thread( run_ir_monitor, (lirc_device, ) )
    except:
        print("Error: unable to start thread run_ir_monitor")

#-----------------------------------------------------------------#
#             watch volume changes                                #
#-----------------------------------------------------------------#
def control_watch():
    global volume
    poll = select.poll()
    descriptors = mixer.polldescriptors()
    poll.register(descriptors[0][0])
    while True:
        events = poll.poll()
        mixer.handleevents()
        for e in events:
            alsa_val = mixer.getvolume()
            value = alsa_val[0]
            volume = value

#--------- start thread for watching volume change ----------------------------#
def run_control_watch():
    try:
        _thread.start_new_thread( control_watch, () )
    except:
        print("Error: unable to start thread control watch")

#-----------------------------------------------------------------#
#             main programm                                       #
#-----------------------------------------------------------------#
init()
run_control_watch()
run_ir_monitor(lirc_device)
while True:
    time.sleep(100)
