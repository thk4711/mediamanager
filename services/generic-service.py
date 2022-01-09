#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import json
import re
import argparse
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
    script_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_path)
    parser = argparse.ArgumentParser(description='generic service')
    parser.add_argument('-p', '--port', type=int, help='WEB server port', required=True)
    args = parser.parse_args()
    port = args.port

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
    meta_data['playstatus']  = False
    return(bytes(json.dumps(meta_data), 'utf-8'))

#------------------------------------------------------------------------------#
#                  get play status                                             #
#------------------------------------------------------------------------------#
def get_play_status():
    play_status = 'NO'
    return(bytes(play_status, 'utf-8'))

#------------------------------------------------------------------------------#
#           previous station                                                   #
#------------------------------------------------------------------------------#
def prev():
    pass
#------------------------------------------------------------------------------#
#           start playback                                                     #
#------------------------------------------------------------------------------#
def play():
    pass

#------------------------------------------------------------------------------#
#           stop playback                                                      #
#------------------------------------------------------------------------------#
def pause():
    pass

#------------------------------------------------------------------------------#
#           next station                                                       #
#------------------------------------------------------------------------------#
def next():
    pass

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
