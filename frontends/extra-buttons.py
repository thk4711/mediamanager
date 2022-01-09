#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import lib.common as common
import argparse

Button_1 = 16
Button_2 = 13
Button_3 = 6
Button_4 = 5

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

    parser = argparse.ArgumentParser(description='handle extra buttons')
    parser.add_argument('-p', '--port', type=int, help='manager port', required=True)
    parser.add_argument('-ho', '--host', type=str, help='manager host', required=False, default='localhost')
    parser.add_argument('-m', '--mixer', type=str, help='volume mixer name', required=False)
    args = parser.parse_args()
    port = args.port
    host = args.host

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
