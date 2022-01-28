#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import json
import dbus
import time
import subprocess
import argparse
import lib.common as common

SERVICE_NAME = "org.bluez"
ADAPTER_NAME = SERVICE_NAME + ".MediaPlayer1"
MANAGER_NAME = "org.freedesktop.DBus.ObjectManager"
adapter = None
player  = None
meta_data   = {}
connected   = False

#------------------------------------------------------------------------------#
#        init plugin                                                           #
#------------------------------------------------------------------------------#
def init():
    global meta_data
    global port
    meta_data['track']  = ""
    meta_data['album']  = ""
    meta_data['artist'] = ""
    meta_data['playstatus'] = False
    meta_data['cover']  = "images/black.png"
    parser = argparse.ArgumentParser(description='media helper')
    parser.add_argument('-p', '--port', type=int, help='WEB server port', required=True)
    args = parser.parse_args()
    port = args.port
    return_code = subprocess.call("echo 'discoverable on\nquit' | /usr/bin/bluetoothctl > /dev/null 2>&1", shell=True)

#------------------------------------------------------------------------------#
#        start plugin                                                          #
#------------------------------------------------------------------------------#
def module_start():
    return_code = subprocess.call("/bin/systemctl restart bluetooth.service > /dev/null 2>&1", shell=True)
    return_code = subprocess.call("echo 'power on\nquit' | /usr/bin/bluetoothctl > /dev/null 2>&1", shell=True)

#------------------------------------------------------------------------------#
#        stop plugin                                                           #
#------------------------------------------------------------------------------#
def module_stop():
    print('STOPPING')
    #return_code = subprocess.call("/bin/systemctl stop bluetooth.service > /dev/null 2>&1", shell=True)
    return_code = subprocess.call("echo 'power off\nquit' | /usr/bin/bluetoothctl", shell=True)

#------------------------------------------------------------------------------#
#       init dbus interface                                                    #
#------------------------------------------------------------------------------#
def init_dbus_interface():
    global adapter
    global player
    global connected
    connected = True
    try:
        bus = dbus.SystemBus()
        service = bus.get_object(SERVICE_NAME, "/")
        manager = dbus.Interface(service, MANAGER_NAME)
        objects = manager.GetManagedObjects()
        for path, ifaces in objects.items():
            adapter = ifaces.get(ADAPTER_NAME)
            if adapter:
                media = bus.get_object(SERVICE_NAME, path)
                break
        else:
            connected = False
            return
            raise Exception('no bluetooth adapter found')
        player = dbus.Interface(media, dbus_interface=ADAPTER_NAME)
    except:
        connected = False

#------------------------------------------------------------------------------#
#        report properies                                                      #
#------------------------------------------------------------------------------#
def get_properties():
    props = {}
    props['type']       = 'service'
    props['name']       = 'bluetooth'
    props['short_name'] = 'BT '
    props['controls']   = True
    props['button']     = "&#xF282;"
    return(props)

#------------------------------------------------------------------------------#
#       get metadata from dbus                                                 #
#------------------------------------------------------------------------------#
def get_metadata():
    global meta_data
    meta_data['track']  = ' '
    meta_data['album']  = ' '
    meta_data['artist'] = ' '
    meta_data['playstatus'] = False
    meta_data['cover']  = 'images/pause.png'
    play_status = False
    init_dbus_interface()
    if connected:
        try:
            status = adapter.get('Status')
            if status == 'playing':
                data = adapter.get('Track')
                if data.get('Title') != None:
                    meta_data['track'] = data.get('Title')
                if data.get('Album') != None:
                    meta_data['album'] = data.get('Album')
                if data.get('Artist') != None:
                    meta_data['artist'] = data.get('Artist')
                meta_data['playstatus'] = True
                meta_data['cover']  = 'images/bluetooth.png'
        except:
            a=1
    return(bytes(json.dumps(meta_data), 'utf-8'))

#------------------------------------------------------------------------------#
#      start playback                                                          #
#------------------------------------------------------------------------------#
def play():
    init_dbus_interface()
    if connected:
        player.Play()

#------------------------------------------------------------------------------#
#      stop playback                                                           #
#------------------------------------------------------------------------------#
def pause():
    init_dbus_interface()
    if connected:
        player.Stop()

#------------------------------------------------------------------------------#
#      next track                                                              #
#------------------------------------------------------------------------------#
def next():
    init_dbus_interface()
    if connected:
        player.Next()

#------------------------------------------------------------------------------#
#      previous track                                                          #
#------------------------------------------------------------------------------#
def prev():
    init_dbus_interface()
    if connected:
        player.Previous()
        player.Previous()

#------------------------------------------------------------------------------#
#                  get play status                                             #
#------------------------------------------------------------------------------#
def get_play_status():
    play_status = 'NO'
    init_dbus_interface()
    if connected:
        status = adapter.get('Status')
        if status == 'playing':
            play_status = 'YES'
    return(bytes(play_status, 'utf-8'))

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
        return(get_play_status())
    return(bytes('OK', 'utf-8'))

#------------------------------------------------------------------------------#
#           main program                                                       #
#------------------------------------------------------------------------------#
init()
common.http_get_handler = respond_to_get_request
common.run_http(port)
while True:
    time.sleep(2000)
