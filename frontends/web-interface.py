#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from cgi import parse_header, parse_multipart
from urllib.parse import parse_qs
import asyncio
import websockets
import json
import time
import threading
#import _thread
import argparse
import os
import pathlib
import lib.common as common

old_metadata = {}
metadata = {}
has_changed = False

#------------------------------------------------------------------------------#
#                do some things at the beginning                               #
#------------------------------------------------------------------------------#
def init():
    global host
    global port
    global config
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/web-interface.conf')
    args = common.init_frontend()
    port = args.port
    host = args.host
    common.run_control_watch()

#------------------------------------------------------------------------------#
#           read content of file in bin mode                                   #
#------------------------------------------------------------------------------#
def read_bin_file(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'rb') as file:
            data = file.read()
        return(data)
    else:
        print(file_name, 'not found')
        return(bytes('Not found', 'utf-8'))

#------------------------------------------------------------------------------#
#                       handle http post request                               #
#------------------------------------------------------------------------------#
def respond_to_post_request(path, post_data):
    global remote_cmd
    global data_changed
    global web_ui_change
    data_changed = True
    #print('>>>>POST->:', path )
    if path == '/mode':
        mode = post_data['mode'][0]
        switch_to(mode)
    if path == '/smode':
        mode_num = post_data['mode'][0]
        mode = mode_order[int(mode_num)]
        #print('smode', mode)
        #remote_cmd = True
        switch_to(mode)
    if path == '/setcontrols':
        control = post_data['control'][0]
        value   = post_data['value'][0]
        set_control(control,int(value))
        web_ui_change = True
    if path == '/setrcontrols':
        control = post_data['control'][0]
        value = post_data['value'][0]
        #print('setting', control, value)
        remote_cmd = True
        set_control(control,int(value))

#------------------------------------------------------------------------------#
#                       handle http get request                                #
#------------------------------------------------------------------------------#
def respond_to_get_request(path):
    global active_output
    if path == '/':
        path = '/index.html'
    if path in '/next/prev/play/pause/toggle/shift':
        str = path.replace('/','')
        common.get_data(host, port, str)
    elif '/volume' in path:
        data = split_path(path)
        common.volume = int(split_path(path)['volume'])
        common.mixer.setvolume(common.volume)
        return(bytes('OK', 'utf-8'))
    elif '/coverimage/' in path:
        data = get_cover_image(path)
        return(data)
    elif '/metadata' in path:
        return(common.get_data(host, port, 'metadata'))
    elif '/configdata' in path:
        data = {}
        data['web_socket_port'] = config['general']['web_socket_port']
        return(bytes(json.dumps(data), 'utf-8'))
    else:
        file_name = path.lstrip('/')
        return(read_bin_file('webui/' + file_name))
    return(bytes('OK', 'utf-8'))

#------------------------------------------------------------------------------#
#                       split path                                             #
#------------------------------------------------------------------------------#
def split_path(path):
    path = path[1:]
    data = {}
    elements = path.split('/')
    for element in elements:
        try:
            key, value = element.split('=',2)
            data[key] = value
        except:
            pass
    return(data)

#------------------------------------------------------------------------------#
#                        get coverimage                                        #
#------------------------------------------------------------------------------#
def get_cover_image(image_name):
    new_image = image_name.replace('/coverimage/','')
    if 'external_' in new_image:
        data = common.get_data(host, port,'coverimage/cover=' + new_image)
    else:
        data = read_bin_file(os.getcwd() + '/' + new_image)
    return data

#------------------------------------------------------------------------------#
#                  check for metadata changes                                  #
#------------------------------------------------------------------------------#
def detect_metadata_changes():
    global metadata
    global old_metadata
    global has_changed
    str_data = common.get_data(host, port, 'metadata')
    metadata = json.loads(str_data.decode('utf-8'))
    for item in metadata:
        if item in old_metadata:
            if metadata[item] != old_metadata[item]:
                has_changed = True
        else:
            has_changed = True
    old_metadata = metadata

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
        data = respond_to_get_request(path)
        self.wfile.write(data)
    # process post requests
    def do_POST(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        path = self.path
        if ctype == 'multipart/form-data':
            post_data = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            post_decoded = self.rfile.read(length).decode('utf-8')
            post_data = parse_qs(post_decoded,
                                keep_blank_values=1,
                                encoding="utf-8",
                                errors="strict",
                                )
        else:
            post_data = {}
        respond_to_post_request(path, post_data)
        self._set_headers()
        self.wfile.write(bytes('ok', 'utf-8'))
    # send headder
    def do_HEAD(self):
        self._set_headers()
    def log_message(self, format, *args):
        return

#------------------------------------------------------------------------------#
#           run the http server in backgroung                                  #
#------------------------------------------------------------------------------#
def run_http():
    server_class=HTTPServer
    handler_class=Server
    port = config['general']['web_server_port']
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('starting http server at port',  port)
    http_thread = threading.Thread(target = httpd.serve_forever, args=())
    http_thread.daemon = True
    http_thread.start()

#------------------------------------------------------------------------------#
#           send updated data using websocket                                  #
#------------------------------------------------------------------------------#
async def ws_update(vu_socket, path):
    global has_changed
    count = 0
    while True:
        if has_changed:
            try:
                await vu_socket.send(json.dumps(metadata))
                has_changed = False
            except:
                pass
        if count > 50:
            try:
                await vu_socket.send(json.dumps(metadata))
                has_changed = False
                count = 0
            except:
                pass
        else:
            count = count + 1
        await asyncio.sleep(0.1)

#------------------------------------------------------------------------------#
#           run the web socket server                                          #
#------------------------------------------------------------------------------#
def run_ws():
    port = config['general']['web_socket_port']
    print('starting websocket server at port', port )
    update_server = websockets.serve(ws_update, '*', port)
    asyncio.get_event_loop().run_until_complete(update_server)
    update_thread = threading.Thread(target = asyncio.get_event_loop().run_forever, args=())
    update_thread.daemon = True
    update_thread.start()

#------------------------------------------------------------------------------#
#           main program                                                       #
#------------------------------------------------------------------------------#
if __name__ == "__main__":
    init()
    run_http()
    run_ws()
    while True:
        detect_metadata_changes()
        time.sleep(1)
