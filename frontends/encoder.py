#!/usr/bin/python3
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time
import lib.common as common
import pathlib
import json

#------------------------------------------------------------------------------#
#        report properies                                                      #
#------------------------------------------------------------------------------#
def init():
    global host
    global port
    global config_port
    global config
    global ENCODER_1_LAST
    global hardware
    ENCODER_1_LAST  = (0,1,1)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/encoder.conf')
    hardware = common.get_hardware_conf(config)
    GPIO.setup(hardware['GPIO']['encoder_button_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(hardware['GPIO']['encoder_pin_1'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(hardware['GPIO']['encoder_pin_2'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(hardware['GPIO']['encoder_button_pin'], GPIO.FALLING, callback=handle_button, bouncetime=300)
    args = common.init_frontend()
    port = args.port
    host = args.host
    config_port = args.configport
    common.run_control_watch()

#------------------------------------------------------------------------------#
#           handle button press                                                #
#------------------------------------------------------------------------------#
def handle_button(pin):
    time.sleep(0.1)
    if GPIO.input(pin) == False:
        if pin == hardware['GPIO']['encoder_button_pin']:
            common.get_data(host,port,config['general']['button_action'])

#------------------------------------------------------------------------------#
#                handle encoder                                                #
#------------------------------------------------------------------------------#
def handle_encoder():
    clkLastState = GPIO.input(hardware['GPIO']['encoder_pin_1'])
    while True:
        clkState = GPIO.input(hardware['GPIO']['encoder_pin_1'])
        dtState = GPIO.input(hardware['GPIO']['encoder_pin_2'])
        if clkState != clkLastState:
            if dtState != clkState:
                common.volume += 1
            else:
                common.volume -= 1
            if common.volume > 100:
                common.volume = 100
            if common.volume < 0:
                common.volume = 0
            common.mixer.setvolume(common.volume)
        clkLastState = clkState
        time.sleep(0.004)

#------------------------------------------------------------------------------#
#                       handle http get request                                #
#------------------------------------------------------------------------------#
def handler(data):
    if 'action' not in data:
        return(bytes('failed', 'utf-8'))
    if data['action'] == 'hwinfo':
        return(bytes(json.dumps(hardware), 'utf-8'))
    return(bytes('OK', 'utf-8'))

#------------------------------------------------------------------------------#
#           read encoder pins in loop                                          #
#------------------------------------------------------------------------------#
init()
common.http_get_handler = handler
common.run_http(config_port)
handle_encoder()
