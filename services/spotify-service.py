#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import json
import os
import sys
import time
import urllib
import socket
import argparse
import requests
import lib.common as common

base_url = 'http://localhost:24879/player/'

#------------------------------------------------------------------------------#
#                         do something on startup                              #
#------------------------------------------------------------------------------#
def init():
    global port
    check_port()
    script_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_path)
    parser = argparse.ArgumentParser(description='media manager spotify connect service')
    parser.add_argument('-p', '--port', type=int, help='WEB server port', required=True)
    args = parser.parse_args()
    port = args.port

#------------------------------------------------------------------------------#
#                         check if librespot-java is running                   #
#------------------------------------------------------------------------------#
def check_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 24879))
    if result == 0:
        sock.close()
        return
    print("Please check if SpoCon is configured correctly and running", file = sys.stderr )
    sock.close()
    exit(1)

#------------------------------------------------------------------------------#
#                  get metadata from spotify                                   #
#------------------------------------------------------------------------------#
def get_metadata():
    meta_data = {}
    global current_cover
    try:
        current_track = get_player()
        album = current_track['item']['album']
        current_cover = album['images'][0]['url']
        tmp_cover = current_cover
        tmp_cover=tmp_cover.replace('https://i.scdn.co/image/','')
        meta_data['track']  = current_track['item']['name']
        meta_data['album']  = album['name']
        meta_data['artist'] = album['artists'][0]['name']
        meta_data['cover']  = 'external_' + tmp_cover
        meta_data['playstatus'] = get_play_status()
        if meta_data['playstatus'] == False:
            meta_data['track']  = ''
            meta_data['album']  = ''
            meta_data['artist'] = ''
            meta_data['cover']  = 'images/pause.png'
        return(bytes(json.dumps(meta_data), 'utf-8'))
    except:
        meta_data['track']  = ''
        meta_data['album']  = ''
        meta_data['artist'] = ''
        meta_data['cover']  = 'images/pause.png'
        meta_data['playstatus'] = False
        return(bytes(json.dumps(meta_data), 'utf-8'))

#------------------------------------------------------------------------------#
#                  get play status                                             #
#------------------------------------------------------------------------------#
def get_play_status(mode=False):
    playing = False
    ret_val = False
    ret_str = 'NO'
    try:
        current_track = get_player()
        playing = current_track['is_playing']
    except:
        pass
    if playing == True:
        try:
            path = 'http://localhost:24879/player/current/'
            ret = requests.post(url = path)
            data = ret.json()
            if 'current' in data:
                ret_str = 'YES'
                ret_val = True
                get_player()
        except:
            pass
    if mode:
        return(bytes(ret_str, 'utf-8'))
    return(ret_val)

#------------------------------------------------------------------------------#
#                  get whats currently playing                                 #
#------------------------------------------------------------------------------#
def get_current():
    path = 'http://localhost:24879/player/current/'
    ret = requests.post(url = path)
    return ret.json()

#------------------------------------------------------------------------------#
#                  get player data from API                                    #
#------------------------------------------------------------------------------#
def get_player():
    path = 'http://localhost:24879/web-api/v1/me/player'
    ret = requests.get(url = path)
    return ret.json()

#------------------------------------------------------------------------------#
#          read cover image fom spotify connect web                            #
#------------------------------------------------------------------------------#
def read_cover_image():
    webURL = urllib.request.urlopen(current_cover)
    data = webURL.read()
    return(data)

#------------------------------------------------------------------------------#
#         play next song                                                       #
#------------------------------------------------------------------------------#
def next():
    requests.post(url = base_url + 'next')

#------------------------------------------------------------------------------#
#         play previuous song                                                  #
#------------------------------------------------------------------------------#
def prev():
    requests.post(url = base_url + 'prev')

#------------------------------------------------------------------------------#
#         start playing                                                        #
#------------------------------------------------------------------------------#
def play():
    requests.post(url = base_url + 'resume')

#------------------------------------------------------------------------------#
#         stop playing                                                         #
#------------------------------------------------------------------------------#
def pause():
    requests.post(url = base_url + 'pause')

#------------------------------------------------------------------------------#
#                       handle http get request                                #
#------------------------------------------------------------------------------#
def respond_to_get_request(data):
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
    elif data['action'] == 'metadata':
        return(get_metadata())
    elif data['action'] == 'coverimage':
        return(read_cover_image())
    elif data['action'] == 'getplaystatus':
        return(get_play_status(True))
    return(bytes('OK', 'utf-8'))

#------------------------------------------------------------------------------#
#           main program                                                       #
#------------------------------------------------------------------------------#
init()
common.http_get_handler = respond_to_get_request
common.run_http(port)
while True:
    time.sleep(2000)
