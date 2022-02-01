#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import pathlib
import RPi.GPIO as GPIO
import lib.common as common

#-----------------------------------------------------------------#
#             do some things first                                #
#-----------------------------------------------------------------#
def init():
    global host
    global port
    global config
    global hardware
    global config_port
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/extra-buttons.conf')
    args = common.init_frontend()
    port = args.port
    host = args.host
    config_port = args.configport
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    hardware = common.get_hardware_conf(config)

    for item in hardware['GPIO']:
        if config['general']['debug']:
            print(f'configuring GPIO {hardware["GPIO"][item]}')
        GPIO.setup(hardware['GPIO'][item], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(hardware['GPIO'][item], GPIO.FALLING, callback=handle_button, bouncetime=600)

#------------------------------------------------------------------------------#
#           handle button press                                                #
#------------------------------------------------------------------------------#
def handle_button(pin):
    if config['general']['debug']:
        print(f'Button GPIO {pin} was pressed')
    for item in hardware['GPIO']:
        if pin == hardware['GPIO'][item]:
            if item in config['actions']:
                action = config['actions'][item]
                if config['general']['debug']:
                    print(f'performing: {action}')
                common.get_data(host,port, action)
            else:
                if config['general']['debug']:
                    print(f'no action defined for GPIO {pin}')

#------------------------------------------------------------------------------#
#                       handle http get request                                #
#------------------------------------------------------------------------------#
def handler(data):
    if 'action' not in data:
        return(bytes('failed', 'utf-8'))
    if data['action'] == 'hwinfo':
        return(bytes(json.dumps(hardware), 'utf-8'))
    return(bytes('OK', 'utf-8'))

#---------------- main script -------------------------------------------------#
init()
common.http_get_handler = handler
common.run_http(config_port)
while True:
    time.sleep(1000)
