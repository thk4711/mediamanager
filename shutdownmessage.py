#!/usr/bin/python3
#------------------------------------------------------------------------------#
#         this script will display shutdown message on 16x2 i2c display        #
#------------------------------------------------------------------------------#

import lib.lcddriver as lcddriver
import time
display_width = 16
lcd = lcddriver.lcd(0x27)
lcd.lcd_clear()
lcd.backlight(1)
lcd.lcd_display_string_pos(' shutting down',1,1)
