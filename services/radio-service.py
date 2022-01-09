#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
from mpd import MPDClient, MPDError, CommandError
import json
import re
import argparse
import lib.common as common
import pprint
import os

stations = None
pos = 0
max = 0
current = 0
meta_data = {}
old_meta_data = {}
command_queue = []
play_status = False

#------------------------------------------------------------------------------#
#        init mpd                                                              #
#------------------------------------------------------------------------------#
def init_mpd(my_host="localhost", my_port=6600, playlist="radio"):
    global mpd_client
    global mpd_host
    global mpd_port
    global stations
    global max
    global meta_data
    global port
    global stations
    script_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_path)
    stations = []
    mpd_port = my_port
    mpd_host = my_host
    mpd_client = MPDClient()
    mpd_client.timeout = 20
    mpd_client.idletimeout = None
    conf = common.read_config(script_path + '/radio-service.conf')
    for item in conf:
        station={'name': item, 'url': conf[item]['url'], 'logo': conf[item]['logo']}
        stations.append(station)
    max = len(stations)-1
    meta_data['track']  = ""
    meta_data['album']  = ""
    meta_data['artist'] = ""
    meta_data['cover']  = "images/pause.png"
    meta_data['max']  = max
    meta_data['current']  = 1
    meta_data['playstatus']  = False
    old_meta_data['track']  = " "
    old_meta_data['album']  = " "
    old_meta_data['artist'] = " "
    old_meta_data['cover']  = " "
    old_meta_data['max']  = 0
    old_meta_data['current']  = 0
    old_meta_data['playstatus']  = True
    parser = argparse.ArgumentParser(description='media helper')
    parser.add_argument('-p', '--port', type=int, help='WEB server port', required=True)
    args = parser.parse_args()
    port = args.port


#------------------------------------------------------------------------------#
#        connect to mpd                                                        #
#------------------------------------------------------------------------------#
def connect():
    try:
        mpd_client.disconnect()
    except:
        a=1
    try:
        mpd_client.connect(mpd_host, mpd_port)
    except:
        return(False)
    return(True)

#------------------------------------------------------------------------------#
#        disconnect to mpd                                                     #
#------------------------------------------------------------------------------#
def disconnect():
    try:
        mpd_client.disconnect()
    except:
        time.sleep(0.5)
        try:
            mpd_client.disconnect()
        except:
            return(False)
    return(True)

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
    meta_data['max']  = max
    meta_data['playstatus']  = False
    if connect():
        try:
            status = mpd_client.status()
        except:
            return(bytes(json.dumps(meta_data), 'utf-8'))
        if status['state'] == 'play':
            play_status = True
            meta_data['playstatus']  = True
        else:
            play_status = False
            meta_data['playstatus']  = False
            return(bytes(json.dumps(meta_data), 'utf-8'))
        try:
            info = mpd_client.currentsong()
        except:
            return(bytes(json.dumps(meta_data), 'utf-8'))
        if 'name' in info.keys():
            name = info["name"]
            name = name.strip()
        if 'title'in info.keys():
            parts  = re.split("( \- )", info["title"], 2)
            if len(parts) > 1:
                artist=parts[0]
                title=parts[2]
            else:
                artist = info["title"]
        artist=artist.replace(name, "")
        artist=artist.strip()
        title=title.replace(name, "")
        title=title.strip()
        cover = 'images/logos/' + str(pos) + '.png'
        meta_data['track']  = stations[current]['name']
        meta_data['album']  = title
        meta_data['artist'] = artist
        meta_data['cover']  = 'images/logos/' + stations[current]['logo']
        disconnect()
    return(bytes(json.dumps(meta_data), 'utf-8'))

#------------------------------------------------------------------------------#
#                  get play status                                             #
#------------------------------------------------------------------------------#
def get_play_status():
    play_status = 'NO'
    if connect():
        try:
            status = mpd_client.status()
            if status['state'] == 'play':
                play_status = 'YES'
        except:
            a=1
        disconnect()
    return(bytes(play_status, 'utf-8'))

#------------------------------------------------------------------------------#
#           previous station                                                   #
#------------------------------------------------------------------------------#
def prev():
    if current > 0:
        playindex(current - 1)
#------------------------------------------------------------------------------#
#           start playback                                                     #
#------------------------------------------------------------------------------#
def play():
    playindex(current)

#------------------------------------------------------------------------------#
#           stop playback                                                      #
#------------------------------------------------------------------------------#
def pause():
    if connect():
        try:
            mpd_client.stop()
        except:
            a=1
    disconnect()

#------------------------------------------------------------------------------#
#           next station                                                       #
#------------------------------------------------------------------------------#
def next():
    if current == max:
        playindex(0)
    else:
        playindex(current + 1)

#------------------------------------------------------------------------------#
#           play specific station                                                       #
#------------------------------------------------------------------------------#
def playindex(index_string):
    global current
    index = int(index_string)
    current = index
    if connect():
        if index <= max:
            try:
                mpd_client.clear()
                mpd_client.add(stations[index]['url'])
                mpd_client.play()
            except:
                a=1
        disconnect()

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
init_mpd()
common.http_get_handler = handler
common.run_http(port)
while True:
    time.sleep(2000)
