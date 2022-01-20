#!/usr/bin/python3
# -*- coding: utf-8 -*-
import urllib.request
import time
import json
import socket
import alsaaudio
import select
import os
import psutil
import select
import subprocess
import lib.common as common
import lib.es9038q2m as hardware
import _thread
import pprint
import pathlib

#------------------------------------------------------------------------------#
#        initialize manager                                                    #
#------------------------------------------------------------------------------#
def init():
    global mixer
    global active_service
    global volume
    global startport
    script_path = str(pathlib.Path(__file__).parent.absolute())
    volume=0
    config = common.read_config(script_path + '/manager.conf')
    #pprint.pprint(config)
    #exit()
    mixers = alsaaudio.mixers()
    if config['global']['mixer'] in mixers:
        print(f"Using mixer: {config['global']['mixer']}")
    else:
        print(f"Mixer {config['global']['mixer']} not found\nplease adjust manager conf.")
        print('The following mixers are available:')
        for mixer in mixers:
            print(f'  -{mixer}')
        exit(1)
    startport = config['global']['startport']
    process_config(config)
    #pprint.pprint(service_list)
    #exit()
    check_if_running()
    start_processes()
    run_check_processes()
    active_service = config['global']['startupservice']
    mixer = alsaaudio.Mixer(config['global']['mixer'])
    run_volume_watch()
    run_detect_active_service()
    hardware.init()
    hardware.switch_mode(active_service)

#------------------------------------------------------------------------------#
#        process config file                                                   #
#------------------------------------------------------------------------------#
def process_config(config):
    global services
    global frontends
    global service_list
    global ps_list
    global service_order
    ps_list = {}
    services = {}
    frontends = {}
    service_list = {}
    service_order = []
    count = 1
    for section in config:
        if 'type' in config[section]:
            if config[section]['type'] == 'service' and config[section]['enabled'] == True:
                service = config[section]['name']
                services[service] = config[section]
                services[service]['status'] = False
                services[service]['old_status'] = False
                services[service]['port'] = startport + count
                count = count + 1
                cmd = ['./services/' + services[service]['start']]
                cmd.append('-p')
                cmd.append(str(services[service]['port']))
                ps_item = {}
                ps_item['cmd'] = cmd
                ps_item['type'] = 'service'
                ps_list['service-' + service] = ps_item
                item = {}
                item['type'] = services[service]['symbol-type']
                if ( item['type'] == 'font' ):
                    item['symbol'] = services[service]['symbol']
                    item['font'] = services[service]['symbol-font']
                if ( item['type'] == 'svg' ):
                    item['icon1'] = services[service]['icon1']
                    item['icon2'] = services[service]['icon2']
                service_list[service] = item
                service_order.append(service)
            if config[section]['type'] == 'frontend' and config[section]['enabled'] == True:
                frontend = config[section]['name']
                frontends[frontend] = {}
                frontends[frontend]['port'] = startport + count
                count = count + 1
                cmd = ['./frontends/' + config[section]['start']]
                cmd.append('-p')
                cmd.append(str(startport))
                cmd.append('-m')
                cmd.append(config['global']['mixer'])
                cmd.append('-c')
                cmd.append(str(frontends[frontend]['port']))
                print(' '.join(cmd))
                ps_item = {}
                ps_item['cmd'] = cmd
                ps_item['type'] = 'frontend'
                ps_list['frontend-' + frontend] = ps_item

#------------------------------------------------------------------------------#
#        start services and frontends                                          #
#------------------------------------------------------------------------------#
def start_processes():
    for item in ps_list:
        print('starting', item)
        repeat_count = 0
        running = False
        while not running:
            ps_list[item]['proc'] = subprocess.Popen(ps_list[item]['cmd'])
            time.sleep(0.3)
            poll = ps_list[item]['proc'].poll()
            if poll != None:
                repeat_count = repeat_count + 1
            else:
                running = True
            if repeat_count == 3:
                check_if_running(False)
                print('faild to start', item)
                print('please check configuration')
                exit(1)

#------------------------------------------------------------------------------#
#        find out weather somthing is already running                          #
#------------------------------------------------------------------------------#
def check_if_running(display_message=True):
    search = []
    for service in services:
        search.append(services[service]['start'])
        if 'pscheck' in services[service]:
            for element in services[service]['pscheck'].split(','):
                search.append(element)
    for proc in psutil.process_iter():
        kill = False
        cmd_string = ' '.join(proc.cmdline())
        for item in search:
            if item in cmd_string:
                kill = True
                if display_message:
                    print('killing', cmd_string)
        if kill:
            proc.kill()

#------------------------------------------------------------------------------#
#        get metadata from mpd                                                 #
#------------------------------------------------------------------------------#
def get_metadata():
    global meta_data
    meta_data = {}
    data = json.loads(get_data('metadata').decode('utf-8'))
    meta_data['track']  = data['track']
    meta_data['album']  = data['album']
    meta_data['artist'] = data['artist']
    meta_data['cover']  = data['cover']
    meta_data['playstatus']  = data['playstatus']
    meta_data['service'] = active_service
    meta_data['volume'] = volume
    #pprint.pprint(meta_data)
    return(bytes(json.dumps(meta_data), 'utf-8'))

#------------------------------------------------------------------------------#
#        make a http get request                                               #
#------------------------------------------------------------------------------#
def get_data(action,service=None):
    if service == None:
        service = active_service
    if common.check_port(services[service]['port'], services[service]['host']) == False:
        if action == 'metadata':
            data = {}
            data=b'{"track": " ", "album": " ", "artist": " ", "cover": "images/pause.png", "playstatus": false}'
            #return(data)
        else:
            pass
            #return('failed')
    #else:
    #    print('--------> unable to get metadata from port', services[service]['host'], services[service]['port'])
    url = 'http://' + services[service]['host'] + ':' + str(services[service]['port']) + '/action=' + action
    try:
        data = urllib.request.urlopen(url).read()
        #if service == 'Airplay':
        #    print(service, url, data)
    except:
        data = 'failed'
        print(service, 'failed')
    return(data)

#------------------------------------------------------------------------------#
#        start metadata collection                                             #
#------------------------------------------------------------------------------#
def run_detect_active_service():
    try:
        _thread.start_new_thread( detect_active_service, () )
    except:
        print("Error: unable to start thread metadata update")

#------------------------------------------------------------------------------#
#        update meta_data                                                      #
#------------------------------------------------------------------------------#
def detect_active_service():
    global active_service
    while True:
        for service in services:
            try:
                result = get_data('getplaystatus',service).decode("utf-8")
                #print('http_result for', service, result)
            except:
                result = 'NO'
                #print('no http_result for', service)
            if result == 'YES':
                if services[service]['old_status'] == False:
                    if service != active_service:
                        get_data('pause')
                        active_service = service
                        hardware.switch_mode(active_service)
                services[service]['status'] = True
            else:
                services[service]['status'] = False
            if services[service]['old_status'] != services[service]['status']:
                services[service]['old_status'] = services[service]['status']
        time.sleep(2)

#------------------------------------------------------------------------------#
#           start thread volume_watch                                          #
#------------------------------------------------------------------------------#
def run_volume_watch():
    try:
        _thread.start_new_thread( volume_watch, () )
    except:
        print("Error: unable to start thread volume watch")

#------------------------------------------------------------------------------#
#           watch volume changes                                               #
#------------------------------------------------------------------------------#
def volume_watch():
    global volume
    poll = select.poll()
    descriptors = mixer.polldescriptors()
    poll.register(descriptors[0][0])
    #print('starting monitor for alsa control ...')
    while True:
        events = poll.poll()
        mixer.handleevents()
        for e in events:
            alsa_val = mixer.getvolume()
            volume = alsa_val[0]

#------------------------------------------------------------------------------#
#        check if all processes are still running                              #
#------------------------------------------------------------------------------#
def check_processes():
    while True:
        for item in ps_list:
            poll = ps_list[item]['proc'].poll()
            if poll != None:
                print('restarting', item)
                ps_list[item]['proc'] = subprocess.Popen(ps_list[item]['cmd'])
        time.sleep(5)

#------------------------------------------------------------------------------#
#           start thread check processes                                       #
#------------------------------------------------------------------------------#
def run_check_processes():
    try:
        _thread.start_new_thread( check_processes, () )
    except:
        print("Error: unable to start thread check processes")

#------------------------------------------------------------------------------#
#                  shift active service to the next one                        #
#------------------------------------------------------------------------------#
def shift_service(direction='up'):
    global active_service
    count = 0
    for iten in service_order:
        if active_service == service_order[count]:
            if direction == 'up':
                count = count + 1
                if count == len(service_order):
                    count = 0
            else:
                count == count -1
                if count < 0:
                    count = len(service_order - 1)
            active_service = service_order[count]
            hardware.switch_mode(service_order[count])
            return()
        count = count + 1

#------------------------------------------------------------------------------#
#                       handle http get request                                #
#------------------------------------------------------------------------------#
def respond_to_get_request(data):
    global active_service
    if data['action'] == 'play':
        return(get_data('play'))
    elif data['action'] == 'pause':
        return(get_data('pause'))
    elif data['action'] == 'toggle':
        if meta_data['playstatus']:
            return(get_data('pause'))
        else:
            return(get_data('play'))
    elif data['action'] == 'prev':
        return(get_data('prev'))
    elif data['action'] == 'next':
        return(get_data('next'))
    elif data['action'] == 'shift':
        get_data('pause')
        shift_service()
        hardware.switch_mode(active_service)
    elif data['action'] == 'poweroff':
        get_data('pause')
        os.system('/usr/sbin/poweroff')
    elif data['action'] == 'metadata':
        return(get_metadata())
    elif data['action'] == 'coverimage':
        return(get_data('coverimage/cover='+data['cover']))
    elif data['action'] == 'playindex':
        return(get_data('playindex/index='+data['index']))
    elif data['action'] == 'getplaystatus':
        return(get_data('getplaystatus'))
    elif data['action'] == 'switchservice':
        get_data('pause')
        if data['service'] in service_list:
            active_service = data['service']
            hardware.switch_mode(active_service)
    elif data['action'] == 'getservicelist':
        return(bytes(json.dumps(service_list), 'utf-8'))
    return(bytes('OK', 'utf-8'))

init()
common.http_get_handler = respond_to_get_request
common.run_http(startport)
while True:
    time.sleep(200)
