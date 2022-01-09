#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import json
import os
import time
import spotipy
#import spotipy.util as util
import urllib
import socket
import argparse
import requests
import lib.common as common
import _thread

#------------------------------------------------------------------------------#
#                         do something on startup                              #
#------------------------------------------------------------------------------#
def init():
    global username
    global port
    global cache_file
    global scope
    global hostname
    global d_id
    d_id = None
    hostname = socket.gethostname()
    script_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_path)
    scope = 'user-modify-playback-state,user-read-currently-playing,user-read-playback-state'
    get_token()
    d_id = -1
    parser = argparse.ArgumentParser(description='media helper')
    parser.add_argument('-p', '--port', type=int, help='WEB server port', required=True)
    args = parser.parse_args()
    port = args.port

#------------------------------------------------------------------------------#
#                         get a token from spotify                             #
#------------------------------------------------------------------------------#
def get_token():
    global spotifyObject
    global valid_token
    try:
        path = 'http://localhost:24879/token/' + scope
        ret = requests.post(url = path)
        data = ret.json()
        token = data['token']
        valid_token = True
        spotifyObject = spotipy.Spotify(auth=token)
    except:
        #print("Error: cannot get token")
        valid_token = False

#------------------------------------------------------------------------------#
#           read config file                                                   #
#------------------------------------------------------------------------------#
def read_config(config_file):
    if not os.path.isfile(config_file):
        print('ERROR config file', config_file, 'does not exist')
        exit(1)
    conf = {}
    with open(config_file) as f:
        content = f.readlines()
    for line in content:
        if line.startswith("#"):
            continue
        line = line.strip()
        key,value = line.split('=',2)
        key   = key.strip()
        value = value.strip()
        if value.lower() == 'no':
            value = False
        elif value.lower() == 'yes':
            value = True
        conf[key] = value
    return(conf)

#------------------------------------------------------------------------------#
#                  get metadata from spotify                                   #
#------------------------------------------------------------------------------#
def get_metadata():
    meta_data = {}
    global current_cover
    try:
        current_track, success = talk_to_spotify('current_track')
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
        current_track, success = talk_to_spotify('current_track')
        playing = current_track['is_playing']
    except:
        playing = False
    if playing:
        ret_val = get_active()
        if ret_val:
            ret_str = 'YES'
    if mode:
        return(bytes(ret_str, 'utf-8'))
    return(ret_val)

#------------------------------------------------------------------------------#
#                  get active status                                           #
#------------------------------------------------------------------------------#
def get_active():
    active = False
    try:
        devices, success = talk_to_spotify('devices')
        for device in devices['devices']:
            if hostname.upper() in device['name'].upper():
                if device['is_active']:
                    active = True
    except:
        active = False
    return(active)

#------------------------------------------------------------------------------#
#                  get device_id                                               #
#------------------------------------------------------------------------------#
def get_device_id():
    global meta_data
    global d_id
    sleep_time = 1
    while True:
        try:
            devices, success = talk_to_spotify('devices')
            for device in devices['devices']:
                #print(device)
                if hostname in device['name']:
                    d_id = device['id']
                    #print('Device ID', d_id)
                    sleep_time = 20
        except:
            d_id = -1
            #print("unable to get device ID")
        time.sleep(sleep_time)

#------------------------------------------------------------------------------#
#                  make a call to spotify with retry                           #
#------------------------------------------------------------------------------#
def talk_to_spotify(item):
    success = False
    result = None
    try:
        if item == 'devices':
            result = spotifyObject.devices()
        elif item == 'current_track':
            result = spotifyObject.current_user_playing_track()
        elif item == 'next':
            result = spotifyObject.next_track(device_id=d_id)
        elif item == 'prev':
            result = spotifyObject.previous_track(device_id=d_id)
        elif item == 'play':
            result = spotifyObject.start_playback(device_id=d_id)
        elif item == 'pause':
            result = spotifyObject.pause_playback(device_id=d_id)
        success = True
    except:
        get_token()
        try:
            if item == 'devices':
                result = spotifyObject.devices()
            elif item == 'current_track':
                result = spotifyObject.current_user_playing_track()
            elif item == 'next':
                result = spotifyObject.next_track(device_id=d_id)
            elif item == 'prev':
                result = spotifyObject.previous_track(device_id=d_id)
            elif item == 'play':
                result = spotifyObject.start_playback(device_id=d_id)
            elif item == 'pause':
                result = spotifyObject.pause_playback(device_id=d_id)
            success = True
        except:
            pass
            #print('unable to talk to spotify')
    return(result, success)

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
    talk_to_spotify('next')

#------------------------------------------------------------------------------#
#         play previuous song                                                  #
#------------------------------------------------------------------------------#
def prev():
    talk_to_spotify('prev')

#------------------------------------------------------------------------------#
#         start playing                                                        #
#------------------------------------------------------------------------------#
def play():
    talk_to_spotify('play')

#------------------------------------------------------------------------------#
#         stop playing                                                         #
#------------------------------------------------------------------------------#
def pause():
    talk_to_spotify('pause')

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

#--------- start thread for watching volume change ----------------------------#
def run_get_device_id():
    try:
        _thread.start_new_thread( get_device_id, () )
    except:
        print("Error: unable to start thread get_device_id")

#------------------------------------------------------------------------------#
#           main program                                                       #
#------------------------------------------------------------------------------#
init()
run_get_device_id()
common.http_get_handler = respond_to_get_request
common.run_http(port)
while True:
    time.sleep(2000)
