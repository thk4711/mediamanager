#!/usr/bin/python3
import time
import RPi.GPIO as GPIO
import lib.common as common
import pathlib
from pcf8575 import PCF8575

#-----------------------------------------------------------------#
#             do some things first                                #
#-----------------------------------------------------------------#
def init():
    global host
    global port
    global pcf
    global last_port
    global config
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/pfc-buttons.conf')
    INTERRUPT_GPIO = int(config['general']['interrupt_gpio'])
    pcf = PCF8575(int(config['general']['i2c_port_num']), int(config['general']['pcf_address'], 16))
    pcf.port  = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    last_port = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(INTERRUPT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(INTERRUPT_GPIO, GPIO.FALLING, callback=button_pressed_callback, bouncetime=100)
    args = common.init_frontend()
    port = args.port
    host = args.host

#-----------------------------------------------------------------#
#     handle interrupt triggert by state change on pcf8575        #
#-----------------------------------------------------------------#
def button_pressed_callback(channel):
    global count
    now = pcf.port
    count = 0
    for io in now:
        if io != last_port[count]:
            if io == False:
                action = config['actions'][str(count)]
                common.get_data(host,port, action)
            last_port[count] = port
        count = count + 1

#-----------------------------------------------------------------#
#                main loop                                        #
#-----------------------------------------------------------------#
init()
while True:
    time.sleep(1000)
