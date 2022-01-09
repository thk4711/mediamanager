#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import json
import re
import argparse
from smbus import SMBus
import lib.common as common
import pprint
import os

meta_data = {}
play_status = False

#------------------------------------------------------------------------------#
#        init                                                                  #
#------------------------------------------------------------------------------#
def init():
    global port
    global i2cbus
    global i2caddress
    script_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_path)
    parser = argparse.ArgumentParser(description='generic service')
    parser.add_argument('-p', '--port', type=int, help='WEB server port', required=True)
    args = parser.parse_args()
    port = args.port
    i2cbus = SMBus(1)
    i2caddress = 0x05

#------------------------------------------------------------------------------#
#        get metadata from mpd                                                 #
#------------------------------------------------------------------------------#
def send_i2c(command):
    cmds = {'prev': 2, 'next': 1, 'play': 3, 'pause': 4}
    i2cbus.write_byte(i2caddress,cmds[command])

#------------------------------------------------------------------------------#
#        get metadata from mpd                                                 #
#------------------------------------------------------------------------------#
def get_metadata():
    global meta_data
    global play_status
    global current
    name   = ''
    title  = ''
    artist = ''
    meta_data['track']  = ""
    meta_data['album']  = ""
    meta_data['artist'] = ""
    meta_data['cover']  = "images/pause.png"
    meta_data['current']  = 1
    meta_data['playstatus']  = play_status
    return(bytes(json.dumps(meta_data), 'utf-8'))

#------------------------------------------------------------------------------#
#                  get play status                                             #
#------------------------------------------------------------------------------#
def get_play_status():
    if play_status:
        return(bytes('YES', 'utf-8'))
    return(bytes('NO', 'utf-8'))

#------------------------------------------------------------------------------#
#           previous station                                                   #
#------------------------------------------------------------------------------#
def prev():
    send_i2c('prev')
#------------------------------------------------------------------------------#
#           start playback                                                     #
#------------------------------------------------------------------------------#
def play():
    global play_status
    play_status = True
    send_i2c('play')

#------------------------------------------------------------------------------#
#           stop playback                                                      #
#------------------------------------------------------------------------------#
def pause():
    global play_status
    play_status = False
    send_i2c('pause')

#------------------------------------------------------------------------------#
#           next station                                                       #
#------------------------------------------------------------------------------#
def next():
    send_i2c('next')

#------------------------------------------------------------------------------#
#           play specific station                                                       #
#------------------------------------------------------------------------------#
def playindex(index_string):
    pass

#------------------------------------------------------------------------------#
#                       handle http get request                                #
#------------------------------------------------------------------------------#
def handler(data):
    if 'action' not in data:
        return(bytes('failed', 'utf-8'))
    if data['action'] == 'play':
        play()
    elif data['action'] == 'pause':
        pause()
    elif data['action'] == 'prev':
        get_metadata()
        prev()
    elif data['action'] == 'next':
        get_metadata()
        next()
    elif data['action'] == 'playindex':
        get_metadata()
        playindex(data['index'])
    elif data['action'] == 'metadata':
        return(get_metadata())
    elif data['action'] == 'getplaystatus':
        return(get_play_status())
    return(bytes('OK', 'utf-8'))

#------------------------------------------------------------------------------#
#           main program                                                       #
#------------------------------------------------------------------------------#
init()
common.http_get_handler = handler
common.run_http(port)
while True:
    time.sleep(2000)
