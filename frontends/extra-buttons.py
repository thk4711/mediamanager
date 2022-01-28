#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import lib.common as common
import argparse

Button_1 = 12
Button_2 = 24
Button_3 = 25
Button_4 = 22

#-----------------------------------------------------------------#
#             do some things first                                #
#-----------------------------------------------------------------#
def init():
    global host
    global port

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(Button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Button_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Button_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Button_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(Button_1, GPIO.FALLING, callback=handle_button, bouncetime=600)
    GPIO.add_event_detect(Button_2, GPIO.FALLING, callback=handle_button, bouncetime=600)
    GPIO.add_event_detect(Button_3, GPIO.FALLING, callback=handle_button, bouncetime=600)
    GPIO.add_event_detect(Button_4, GPIO.FALLING, callback=handle_button, bouncetime=600)

    args = common.init_frontend()
    port = args.port
    host = args.host
    config_port = args.configport

#------------------------------------------------------------------------------#
#           handle button press                                                #
#------------------------------------------------------------------------------#
def handle_button(pin):
    index = 1
    if pin == Button_1: index = common.get_data(host,port,'shift')
    if pin == Button_2: index = common.get_data(host,port,'prev')
    if pin == Button_3: index = common.get_data(host,port,'toggle')
    if pin == Button_4: index = common.get_data(host,port,'next')

init()
while True:
    time.sleep(1000)
