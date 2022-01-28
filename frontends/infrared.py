#!/usr/bin/python3
# -*- coding: utf-8 -*-

import _thread
import time
import pathlib
import lib.common as common
import os
import json
from evdev import InputDevice, categorize, ecodes, list_devices

#### enable debug to see IR codes received
debug = True

#-----------------------------------------------------------------#
#             do some things at the beginning                     #
#-----------------------------------------------------------------#
def init():
    global lirc_device
    global config
    global args
    os.system('/usr/bin/ir-keytable -p all >/dev/null 2>&1')
    args = common.init_frontend()
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/infrared.conf')
    common.run_control_watch()
    devices = [InputDevice(path) for path in list_devices()]
    for device in devices:
        if device.name == config['general']['device-name']:
            lirc_device = InputDevice(device.path)

#-----------------------------------------------------------------#
#             translate key code to string                        #
#-----------------------------------------------------------------#
def key_code_to_action(code):
    if config['general']['debug']:
        print('code: ', code)
    if str(code) in config['buttons']:
        action = config['buttons'][str(code)]
        if config['general']['debug']:
            print('action:', action)
        if action == 'volume+' : volume_adjust(1)
        elif action == 'volume-' : volume_adjust(-1)

        elif 'station' in action:
            action = action.replace('station=','')
            common.get_data(host,port,'switchservice/service=Radio')
            common.get_data(host,port,'playindex/index=' + action)
        else:
            common.get_data(args.host,args.port,action)
    else:
        pass
        #print('unknown ir code')

#-----------------------------------------------------------------#
#             adjust volume                                       #
#-----------------------------------------------------------------#
def volume_adjust(diff):
    common.volume = common.volume + diff
    if common.volume > 100:
        common.volume = 100
    if common.volume < 0:
        common.volume = 0
    common.mixer.setvolume(common.volume)

#-----------------------------------------------------------------#
#                 background thred to get keycode                 #
#-----------------------------------------------------------------#
def run_ir_monitor(lirc_device):
    repeat_count = 0
    last_value = None
    last_time = round(time.time() * 1000)
    for event in lirc_device.read_loop():
        if event.type == 4:
            value = abs(event.value)
            now = round(time.time() * 1000)
            diff = now -last_time
            if diff > 300:
                repeat_count = 0
                last_value = None
            if last_value == value:
                repeat_count = repeat_count +1
                if repeat_count > 4:
                    #print('value', value)
                    key_code_to_action(value)
            else:
                repeat_count = 0
                #print('value', value)
                key_code_to_action(value)
            last_value = value
            last_time = now

#------------------------------------------------------------------------------#
#           start thread ifrared monitor                                       #
#------------------------------------------------------------------------------#
def ir_monitor():
    try:
        _thread.start_new_thread( run_ir_monitor, (lirc_device, ) )
    except:
        print("Error: unable to start thread run_ir_monitor")

#------------------------------------------------------------------------------#
#                       handle http get request                                #
#------------------------------------------------------------------------------#
def handler(data):
    if 'action' not in data:
        return(bytes('failed', 'utf-8'))
    if data['action'] == 'hwinfo':
        #hardware = common.get_kernel_gpio_usage()
        return(bytes(json.dumps({'GPIO': common.get_kernel_gpio_usage()}), 'utf-8'))
    return(bytes('OK', 'utf-8'))

#------------------------------------------------------------------------------#
#           main programm                                                      #
#------------------------------------------------------------------------------#
init()
common.http_get_handler = handler
common.run_http(args.configport)
run_ir_monitor(lirc_device)
while True:
    time.sleep(100)
