#!/usr/bin/python3
# -*- coding: utf-8 -*-

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import socket
import urllib.request
import os
import re
import argparse
import alsaaudio
import _thread
import select
import smbus
import errno

http_get_handler = None

#------------------------------------------------------------------------------#
#        make a http get request                                               #
#------------------------------------------------------------------------------#
def get_data(host,port,action):
    if check_port(port, host):
        return('failed')
    url = 'http://' + host + ':' + str(port) + '/action=' + action
    try:
        data = urllib.request.urlopen(url).read()
    except:
        data = 'failed'
    return(data)

#------------------------------------------------------------------------------#
#        get command line args for frontend                                    #
#------------------------------------------------------------------------------#
def init_frontend():
    global mixer
    global volume
    global old_volume
    global blocked
    blocked = False
    parser = argparse.ArgumentParser(description='media helper')
    parser.add_argument('-p', '--port', type=int, help='manager port', required=True)
    parser.add_argument('-ho', '--host', type=str, help='manager host', required=False, default='localhost')
    parser.add_argument('-m', '--mixer', type=str, help='volume mixer name', required=True)
    args = parser.parse_args()
    mixer_name = args.mixer
    mixer = alsaaudio.Mixer(mixer_name)
    alsa_val = mixer.getvolume()
    value = alsa_val[0]
    volume = value
    old_volume = -1
    return(args)

#------------------------------------------------------------------------------#
#                        watch volume changes                                  #
#------------------------------------------------------------------------------#

def control_watch():
    global volume
    poll = select.poll()
    descriptors = mixer.polldescriptors()
    poll.register(descriptors[0][0])
    while True:
        if blocked == False:
            events = poll.poll()
            mixer.handleevents()
            for e in events:
                alsa_val = mixer.getvolume()
                value = alsa_val[0]
                volume = value
                time.sleep(0.5)

#------------------------------------------------------------------------------#
#               start thread for watching volume change                        #
#------------------------------------------------------------------------------#
def run_control_watch():
    try:
        _thread.start_new_thread( control_watch, () )
    except:
        print("Error: unable to start thread control watch")

#------------------------------------------------------------------------------#
#        check if port is open                                                 #
#------------------------------------------------------------------------------#
def check_port(port,host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host,port))
    is_not_working = True
    if result == 0:
        is_not_working = False
    else:
        print('Port', port, 'is not open')
    return(is_not_working)

#------------------------------------------------------------------------------#
#           http request handler                                               #
#------------------------------------------------------------------------------#
class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        path = self.path
        if '.css' in path:
            self.send_header('Content-type', 'text/css')
        elif '.js' in path:
            self.send_header('Content-type', 'text/javascript')
        else:
            self.send_header('Content-type', 'text/html')
        self.end_headers()
    # process get requests
    def do_GET(self):
        self._set_headers()
        path = self.path
        data = http_get_handler(split_path(path))
        self.wfile.write(data)
    # send headder
    def do_HEAD(self):
        self._set_headers()
    def log_message(self, format, *args):
        return

#------------------------------------------------------------------------------#
#           run the http server in backgroung                                  #
#------------------------------------------------------------------------------#
def run_http(port):
    server_class=HTTPServer
    handler_class=Server
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    http_thread = threading.Thread(target = httpd.serve_forever, args=())
    http_thread.daemon = True
    http_thread.start()

#------------------------------------------------------------------------------#
#                       split path                                             #
#------------------------------------------------------------------------------#
def split_path(path):
    path = path[1:]
    data = {}
    elements = path.split('/')
    for element in elements:
        key, value = element.split('=',2)
        data[key] = value
    return(data)

#------------------------------------------------------------------------------#
#           read config file                                                   #
#------------------------------------------------------------------------------#
def read_config(config_file):
    section = ''
    if not os.path.isfile(config_file):
        print('ERROR config file', config_file, 'does not exist')
        exit(1)
    conf = {}
    with open(config_file) as f:
        content = f.readlines()
    for line in content:
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.startswith("["):
            section = re.findall(r"^\[(.+)\]$", line)[0]
            conf[section] = {}
            continue
        if '=' in line:
            key,value = line.split('=',1)
            key   = key.strip()
            value = value.strip()
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            elif re.match(r'^([\d]+)$', value) :
                value = int(value)
            conf[section][key] = value
    return(conf)

#-----------------------------------------------------------------#
#             check if i2c device is present                      #
#-----------------------------------------------------------------#
def check_smbus(device_address, bus_number = 1):
    try:
        bus = smbus.SMBus(bus_number)
        bus.write_byte(device_address, 0)
        print("Found {0}".format(hex(device_address)))
    except:
        print(f'unable to fine i2c device {hex(device_address)} on bus {bus_number}')
        exit(1)
