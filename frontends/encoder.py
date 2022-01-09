#!/usr/bin/python3
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time
import lib.common as common
import pathlib

#------------------------------------------------------------------------------#
#        report properies                                                      #
#------------------------------------------------------------------------------#
def init():
    global host
    global port
    global config
    global ENCODER_1_LAST
    ENCODER_1_LAST  = (0,1,1)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/encoder.conf')
    GPIO.setup(int(config['general']['encoder_button_pin']), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(int(config['general']['encoder_pin_1']), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(int(config['general']['encoder_pin_2']), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(int(config['general']['encoder_button_pin']), GPIO.FALLING, callback=handle_button, bouncetime=300)
    args = common.init_frontend()
    port = args.port
    host = args.host
    common.run_control_watch()

#------------------------------------------------------------------------------#
#           handle button press                                                #
#------------------------------------------------------------------------------#
def handle_button(pin):
    time.sleep(0.1)
    if GPIO.input(pin) == False:
        if pin == int(config['general']['encoder_button_pin']):
            common.get_data(host,port,config['general']['button_action'])

#------------------------------------------------------------------------------#
#           read encoder pins in loop                                          #
#------------------------------------------------------------------------------#
init()
clkLastState = GPIO.input(int(config['general']['encoder_pin_1']))
while True:
    clkState = GPIO.input(int(config['general']['encoder_pin_1']))
    dtState = GPIO.input(int(config['general']['encoder_pin_2']))
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
    time.sleep(0.003)
