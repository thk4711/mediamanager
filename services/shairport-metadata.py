#!/usr/bin/python3
import re, sys
import base64
import json
import uuid
import hashlib
import pprint

meta_data = {}
meta_data['track']    = ''
meta_data['album']    = ''
meta_data['artist']   = ''
meta_data['filetype'] = ''
meta_data['md5']      = ''

old_meta_data = {}
old_meta_data['track']    = ''
old_meta_data['album']    = ''
old_meta_data['artist']   = ''
old_meta_data['filetype'] = ''
old_meta_data['md5']      = ''

#------------------------------------------------------------------------------#
#                       find out item type                                     #
#------------------------------------------------------------------------------#
def start_item(line):
    regex = r"<item><type>(([A-Fa-f0-9]{2}){4})</type><code>(([A-Fa-f0-9]{2}){4})</code><length>(\d*)</length>"
    matches = re.findall(regex, line)
    typ = bytes.fromhex(matches[0][0]).decode()
    code = bytes.fromhex(matches[0][2]).decode()
    length = int(matches[0][4])
    return (typ, code, length)

#------------------------------------------------------------------------------#
#        identify line content                                                 #
#------------------------------------------------------------------------------#
def start_data(line):
    try:
        assert line == '<data encoding="base64">\n'
    except AssertionError:
        if line.startswith("<data"):
            return 0
        return -1
    return 0

#------------------------------------------------------------------------------#
#        decode data                                                           #
#------------------------------------------------------------------------------#
def read_data(line, length, decode):
    data = ""
    try:
        parts = line.split('</data>')
        if decode:
            data = base64.b64decode(parts[0]).decode()
        else:
            data = base64.b64decode(parts[0])
    except:
        pass
    return data

#------------------------------------------------------------------------------#
#                     find image type                                          #
#------------------------------------------------------------------------------#
def guessImageMime(magic):
    if magic.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif magic.startswith('\x89PNG\r\n\x1a\r'):
        return 'png'
    else:
        return "jpg"

#------------------------------------------------------------------------------#
#        update json file with metadata                                        #
#------------------------------------------------------------------------------#
def update_json():
    items = ['track', 'album', 'artist', 'filetype', 'md5']
    changed = False
    for item in items:
        if old_meta_data[item] != meta_data[item]:
            changed = True
            old_meta_data[item] = meta_data[item]
    if changed:
        j_string = json.dumps(meta_data)
        file = open('/tmp/shairport-metadata.json', 'w')
        file.write(j_string)
        file.close()

#------------------------------------------------------------------------------#
#                           main script part                                   #
#------------------------------------------------------------------------------#
if __name__ == "__main__":
    metadata = {}
    fi = sys.stdin
    while True:
        line = sys.stdin.readline()
        if not line:    #EOF
            break
        sys.stdout.flush()
        if not line.startswith("<item>"):
            continue
        typ, code, length = start_item(line)

        data = ""
        if (length > 0):
            r = start_data(sys.stdin.readline())
            if (r == -1):
                continue
            if (typ == "ssnc" and code == "PICT"):
                data = read_data(sys.stdin.readline(), length, False)
            else:
                data = read_data(sys.stdin.readline(), length, True)
        # Everything read
        if (typ == "core"):
            if (code == "asal"):
                meta_data['album']  = data
            elif (code == "asar"):
                meta_data['artist']  = data
            elif (code == "minm"):
                meta_data['track'] = data
        if (typ == "ssnc" and code == "pfls"):
            metadata = {}
        if (typ == "ssnc" and code == "pend"):
            metadata = {}
        if (typ == "ssnc" and code == "PICT"):
            if (len(data) != 0):
                file_type = guessImageMime(data)
                filename = '/tmp/shairport-image.' + file_type
                file = open(filename, 'wb')
                file. write(data)
                file.close()
                meta_data['filetype'] = file_type
                meta_data['md5'] = hashlib.md5(data).hexdigest()
                update_json()
            sys.stdout.flush()
        if (typ == "ssnc" and code == "mden"):
            update_json()
