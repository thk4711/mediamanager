#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import json
import os
import psutil
import subprocess
import argparse
import lib.common as common

#------------------------------------------------------------------------------#
#        start some processes in background                                    #
#------------------------------------------------------------------------------#
def init():
    global port
    global script_path
    script_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_path)
    data = {'track':'','album':'','artist':'','filetype':'','md5':''}
    j_string = json.dumps(data)
    file = open('/tmp/shairport-metadata.json', 'w')
    file.write(j_string)
    file.close()
    pid=os.fork()
    if pid==0:
        os.system("cat /tmp/shairport-sync-metadata | " + script_path + "/shairport-metadata.py")
        exit()
    parser = argparse.ArgumentParser(description='media helper')
    parser.add_argument('-p', '--port', type=int, help='WEB server port', required=True)
    args = parser.parse_args()
    port = args.port

#------------------------------------------------------------------------------#
#           interact with dbus interface                                       #
#------------------------------------------------------------------------------#
def talk_to_dbus(action):
    method = ''
    ret = ''
    cmd = '/usr/bin/qdbus --system org.gnome.ShairportSync /org/gnome/ShairportSync '
    if action == 'next':
        method = 'org.gnome.ShairportSync.RemoteControl.Next'
    elif action == 'prev':
        method = 'org.gnome.ShairportSync.RemoteControl.Previous'
    elif action == 'play':
        method = 'org.gnome.ShairportSync.RemoteControl.Play'
    elif action == 'pause':
        method = 'org.gnome.ShairportSync.RemoteControl.Pause'
    ret_code = os.system(cmd + method)
    if (ret_code) != 0:
        ret = ('action ' + action + ' failed')
    else:
        ret = 'OK'
    return(ret)

#------------------------------------------------------------------------------#
#                           execute comand on OS level                         #
#------------------------------------------------------------------------------#
def execute_os_command(command):
    cmd_array = command.split()
    process = subprocess.Popen( cmd_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    out = out.decode('utf8')
    lines = out.split('\n')
    return(lines, err)

#------------------------------------------------------------------------------#
#          read cover image fom spotify connect web                            #
#------------------------------------------------------------------------------#
def read_cover_image(cover_uri):
    data = None
    image_path = '/tmp/shairport-image.'
    if '.jpg' in cover_uri:
        image_path = image_path + 'jpg'
    elif '.jpeg' in cover_uri:
        image_path = image_path + 'jpeg'
    elif '.png' in cover_uri:
        image_path = image_path + 'png'
    else:
        return(bytes('Not found', 'utf-8'))
    with open(image_path, 'rb') as file:
        data = file.read()
    return(data)

#------------------------------------------------------------------------------#
#                  get metadata from spotify-connect-web                       #
#------------------------------------------------------------------------------#
def get_metadata():
    meta_data = {}
    data = json.load(open('/tmp/shairport-metadata.json'))
    meta_data['track']  = data['track']
    meta_data['album']  = data['album']
    meta_data['artist'] = data['artist']
    meta_data['playstatus'] = get_play_status()
    if meta_data['playstatus']:
        meta_data['cover']  = 'external_' + data['md5'] + '.' + data['filetype']
    else:
        meta_data['cover']  = 'images/pause.png'
    return(bytes(json.dumps(meta_data), 'utf-8'))

#------------------------------------------------------------------------------#
#                  get play status                                             #
#------------------------------------------------------------------------------#
def get_play_status(mode=False):
    cmd = '/usr/bin/qdbus --system org.gnome.ShairportSync /org/gnome/ShairportSync org.gnome.ShairportSync.RemoteControl.PlayerState'
    lines,error = execute_os_command(cmd)
    result = False
    ex_result = 'NO'
    if 'Playing' in lines[0]:
        result = True
        ex_result = 'YES'
    if mode:
        return(bytes(ex_result, 'utf-8'))
    return(result)


#------------------------------------------------------------------------------#
#                  get play status                                             #
#------------------------------------------------------------------------------#
def get_active():
    active_status = 'active'
    if active_status == 'active':
        return(True)
    else:
        return(False)

#------------------------------------------------------------------------------#
#         play next song                                                       #
#------------------------------------------------------------------------------#
def next():
    talk_to_dbus('next')

#------------------------------------------------------------------------------#
#         play previuous song                                                  #
#------------------------------------------------------------------------------#
def prev():
    talk_to_dbus('prev')

#------------------------------------------------------------------------------#
#         start playing                                                        #
#------------------------------------------------------------------------------#
def play():
    talk_to_dbus('play')

#------------------------------------------------------------------------------#
#         stop playing                                                         #
#------------------------------------------------------------------------------#
def pause():
    talk_to_dbus('pause')

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
        cover_uri = data['cover'].replace('/coverimage/','')
        return(read_cover_image(cover_uri))
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
