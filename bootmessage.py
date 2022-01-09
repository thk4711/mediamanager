#!/usr/bin/python3

import lib.lcddriver as lcddriver
display_width = 16
lcd = lcddriver.lcd(0x27)
lcd.lcd_clear()
lcd.backlight(1)
lcd.lcd_display_string_pos('booting ...',1,3)
