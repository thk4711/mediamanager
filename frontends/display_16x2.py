#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import lib.lcddriver as lcddriver
import json
import pathlib
from datetime import datetime
import lib.common as common

pauseChar = [0b11011,0b11011,0b11011,0b11011,0b11011,0b11011,0b11011,0b00000]
playChar  = [0b01000,0b01100,0b01110,0b01111,0b01110,0b01100,0b01000,0b00000]

#------------------------------------------------------------------------------#
#        report properies                                                      #
#------------------------------------------------------------------------------#
def init():
    global host
    global port
    global lcd
    global old_time_string
    global meta_data
    global old_meta_data
    global display_width
    meta_data = {}
    old_meta_data = {}
    old_time_string = '00:01'
    meta_data['track']  = " "
    meta_data['playstatus']  = False
    meta_data['service']  = 'Radio'
    meta_data['volume'] = 0
    old_meta_data['track']  = "  "
    old_meta_data['playstatus']  = False
    old_meta_data['service']  = ''
    old_meta_data['volume'] = 1
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/display_16x2.conf')
    lcd = lcddriver.lcd(int(config['general']['display_address'], 16))
    display_width = int(config['general']['display_width'])
    lcd.lcd_clear()
    lcd.backlight(1)
    lcd.lcd_load_custom_chars([pauseChar,playChar])
    args = common.init_frontend()
    port = args.port
    host = args.host
    update_metadata()
    lcd.lcd_display_string_pos(str(common.volume),1,0)
    if meta_data['playstatus']:
        lcd.lcd_display_string_pos(chr(1),1,15)
    else:
        lcd.lcd_display_string_pos(chr(0),1,15)
    common.run_control_watch()

#------------------------------------------------------------------------------#
#        get metadata                                                          #
#------------------------------------------------------------------------------#
def update_metadata():
    global meta_data
    str_data = common.get_data(host,port,'metadata')
    data = json.loads(str_data.decode('utf-8'))
    meta_data['track']  = data['track']
    meta_data['playstatus']  = data['playstatus']
    meta_data['service']  = data['service']

#------------------------------------------------------------------------------#
#   return string with is in the middle of a line                              #
#------------------------------------------------------------------------------#
def print_center(content):
    if len(content) > display_width:
        content = content[:display_width]
    content_length = len(content)
    r_size = content_length + int((display_width - content_length)/2)
    content = content.rjust(r_size, ' ')
    content = content.ljust(display_width, ' ')
    return(content)

#------------------------------------------------------------------------------#
#            update lcd display                                                #
#------------------------------------------------------------------------------#
def update_display():
    global old_time_string
    global old_meta_data
    now = datetime.now()
    time_string = now.strftime("%H:%M")
    if old_time_string != time_string:
        try:
            lcd.lcd_display_string_pos(time_string,1,5)
        except:
            print('unable to write to LCD')
        old_time_string = time_string

    if meta_data['service'] == 'Radio':
        if old_meta_data['service'] != meta_data['service']:
            try:
                lcd.lcd_display_string_pos(print_center(meta_data['service']),2,0)
            except:
                print('unable to write to LCD')
            old_meta_data['service'] = meta_data['service']
        if old_meta_data['track'] != meta_data['track']:
            try:
                if meta_data['playstatus'] == False:
                    lcd.lcd_display_string_pos(print_center('Radio'),2,0)
                else:
                    disp_string = meta_data['track']
                    lcd.lcd_display_string_pos(print_center(disp_string),2,0)
            except:
                print('unable to write to LCD')
            old_meta_data['track'] = meta_data['track']
    else:
        if old_meta_data['service'] != meta_data['service']:
            try:
                lcd.lcd_display_string_pos(print_center(meta_data['service']),2,0)
            except:
                print('unable to write to LCD')
            old_meta_data['service'] = meta_data['service']
    if meta_data['playstatus'] != old_meta_data['playstatus']:
        if meta_data['playstatus'] == True:
            lcd.lcd_display_string_pos(chr(1),1,15)
        else:
            lcd.lcd_display_string_pos(chr(0),1,15)
        old_meta_data['playstatus'] = meta_data['playstatus']
    if common.old_volume != common.volume:
        lcd.lcd_display_string_pos(str(common.volume) + ' ',1,0)
        common.old_volume = common.volume

#------------------------------------------------------------------------------#
#            main loop                                                         #
#------------------------------------------------------------------------------#
init()
count = 0
while True:
    if count > 3:
        update_metadata()
        count = 0
    count = count + 1
    time.sleep(0.2)
    update_display()
