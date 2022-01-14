#!/usr/bin/python3

import os
import re
import subprocess
import sys
import tty
import termios
from shutil import copyfile

#------------------------------------------------------------------------------#
#           execute command on os level                                        #
#------------------------------------------------------------------------------#
def execute_os_command(cmd,ignore_error=False):
    print('executing', cmd)
    return_code = subprocess.call(cmd, shell=True)
    if return_code  != 0:
        print('FAILD to execute', cmd)
        if ignore_error == False:
            exit(1)

#------------------------------------------------------------------------------#
#           read config file                                                   #
#------------------------------------------------------------------------------#
def read_config(config_file):
    section = ''
    if not os.path.isfile(config_file):
        print('ERROR config file', config_file, 'does not exist')
        exit(1)
    conf = {}
    conf['DEBIAN-PACKAGES'] = []
    conf['PIP-PACKAGES'] = []
    conf['PRE-CMD'] = []
    conf['POST-CMD'] = []
    conf['MANUAL-PACKAGES'] = {}
    conf['OS-FILES'] = []
    conf['DO-AS-PI'] = []
    conf['SOUND-CARDS'] = {}
    with open(config_file) as f:
        content = f.readlines()
    for line in content:
        line = line.strip()
        if line.startswith("#") or line == '':
            continue
        if line.startswith("["):
            section = re.findall(r"^\[(.+)\]$", line)[0]
            #conf[section] = {}
            continue
        if section == 'DEBIAN-PACKAGES':
            conf['DEBIAN-PACKAGES'].append(line)
        elif section == 'OS-FILES':
            conf['OS-FILES'].append(line)
        elif section == 'PIP-PACKAGES':
            conf['PIP-PACKAGES'].append(line)
        elif section == 'DO-AS-PI':
            conf['DO-AS-PI'].append(line)
        elif section == 'PRE-CMD':
            conf['PRE-CMD'].append(line)
        elif section == 'POST-CMD':
            conf['POST-CMD'].append(line)
        elif 'MANUAL-PACKAGE' in section:
            pkg_name = section.replace('MANUAL-PACKAGE-', '')
            if pkg_name in conf['MANUAL-PACKAGES']:
                conf['MANUAL-PACKAGES'][pkg_name].append(line)
            else:
                conf['MANUAL-PACKAGES'][pkg_name] = []
                conf['MANUAL-PACKAGES'][pkg_name].append(line)
        elif 'SOUND-CARDS' in section:
            key,value = line.split('=',2)
            key   = key.strip()
            value = value.strip()
            config_string,mixer_name,control = value.split(':',3)
            #print(config_string,mixer_name,control)
            conf['SOUND-CARDS'][key] = {}
            conf['SOUND-CARDS'][key]['CONFIG-STRING'] = config_string
            conf['SOUND-CARDS'][key]['MIXER'] = mixer_name
            conf['SOUND-CARDS'][key]['CONTROL'] = control
        else:
            if section not in conf:
                conf[section] = {}
            if '=' in line:
                key,value = line.split('=',2)
                key   = key.strip()
                value = value.strip()
                if re.match(r'^([\d]+)$', value) :
                    value = int(value)
                if re.match(r'^([\d]+)$', key) :
                    key = int(key)
                conf[section][key] = value
    return(conf)

#------------------------------------------------------------------------------#
#           install manual packages                                            #
#------------------------------------------------------------------------------#
def install_manual_packages():
    for item in conf['MANUAL-PACKAGES']:
        print('installing', item)
        with open('/tmp/tmp_cmd.sh', 'w') as filehandle:
            for cmd in conf['MANUAL-PACKAGES'][item]:
                filehandle.write('%s\n' % cmd)
        execute_os_command('/bin/bash /tmp/tmp_cmd.sh')

#------------------------------------------------------------------------------#
#           do some things as user pi                                          #
#------------------------------------------------------------------------------#
def execute_as_pi():
    print('doing something as user pi')
    with open('/tmp/tmp_pi_cmd.sh', 'w') as filehandle:
        filehandle.write('#!/bin/sh\n')
        for cmd in conf['DO-AS-PI']:
            if cmd.startswith('file'):
                cmd = cmd.replace('file ','')
                source = script_path + '/os-files' + cmd
                file_name = os.path.basename(source)
                execute_os_command('/bin/cp -p ' + source + ' /tmp/')
                cmd = '/bin/cp -p /tmp/' + file_name + ' ' + cmd
            filehandle.write('%s\n' % cmd)
        filehandle.write('echo Done executing as pi\n')
    execute_os_command('chmod +777 /tmp/tmp_pi_cmd.sh')
    execute_os_command('ssh-keygen -b 2048 -t rsa -f /tmp/sshkey -q -N ""')
    execute_os_command('mkdir -p /home/pi/.ssh')
    execute_os_command('chown pi:pi /home/pi/.ssh/')
    execute_os_command('cp /tmp/sshkey.pub /home/pi/.ssh/authorized_keys')
    execute_os_command('chown pi:pi /home/pi/.ssh/authorized_keys')
    execute_os_command('chmod 700 /home/pi/.ssh/')
    execute_os_command('chmod 600 /home/pi/.ssh/authorized_keys')
    execute_os_command('ssh -o StrictHostKeyChecking=no -i /tmp/sshkey pi@localhost /tmp/tmp_pi_cmd.sh')
    execute_os_command('rm /home/pi/.ssh/authorized_keys')
    execute_os_command('rm /tmp/sshkey*')
    execute_os_command('rm /tmp/tmp_pi_cmd.sh')

#------------------------------------------------------------------------------#
#           install debian packages                                            #
#------------------------------------------------------------------------------#
def install_debian_packages():
    cmd_string = '/usr/bin/apt-get -y install --no-install-recommends '
    for package in conf['DEBIAN-PACKAGES']:
        cmd_string = cmd_string + package + ' '
    execute_os_command(cmd_string)

#------------------------------------------------------------------------------#
#           install python modules with pip3                                   #
#------------------------------------------------------------------------------#
def install_pip_packages():
    for package in conf['PIP-PACKAGES']:
        cmd = '/usr/bin/pip3 install ' + package
        execute_os_command(cmd)

#------------------------------------------------------------------------------#
#           search for a line and replace it                                   #
#------------------------------------------------------------------------------#
def search_and_replace(file_name, search_string, replacement_line, add_if_not_found=False, delete=False):
    found = False
    if add_if_not_found and delete:
        print('you cannot add and delete a line at the same time')
        exit(1)
    with open(file_name) as f:
        content = f.readlines()
    f = open(file_name, 'w')
    for line in content:
        #print(line)
        r_line = line.rstrip() + '\n'
        skip = False
        if search_string in r_line:
            found=True
            if delete:
                skip = True
            else:
                print('replaceing: ',line,'->',replacement_line)
                line = replacement_line + '\n'
        if skip == False:
            pass
            f.write(line)
    if found == False and add_if_not_found == True:
        pass
        f.write(replacement_line)
    f.close

#------------------------------------------------------------------------------#
#           fix hostname in raspotify config files                             #
#------------------------------------------------------------------------------#
def fix_hostname():
    hostname = os.uname()[1]
    print(hostname)

    search_and_replace('/opt/spocon/config.toml','deviceName =','deviceName = "' + hostname + '"')

#------------------------------------------------------------------------------#
#           copy file from os_files dir                                        #
#------------------------------------------------------------------------------#
def copy_files():
    for file_name in conf['OS-FILES']:
        cmd = '/bin/cp -p ' + script_path + '/os-files' + file_name + ' ' + file_name
        execute_os_command(cmd)

#------------------------------------------------------------------------------#
#           get files from running system                                      #
#------------------------------------------------------------------------------#
def get_files():
    for file_name in conf['OS-FILES']:
        cmd = '/bin/cp --parent ' + file_name + ' ' + script_path + '/os-files'
        execute_os_command(cmd)

#------------------------------------------------------------------------------#
#           execute pre_cmd commands                                           #
#------------------------------------------------------------------------------#
def execute_pre_cmd():
    for cmd in conf['PRE-CMD']:
        execute_os_command(cmd)

#------------------------------------------------------------------------------#
#           execute post_cmd commands                                          #
#------------------------------------------------------------------------------#
def execute_post_cmd():
    for cmd in conf['POST-CMD']:
        execute_os_command(cmd,True)

#------------------------------------------------------------------------------#
#           read a caracter from stdin                                         #
#------------------------------------------------------------------------------#
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

#------------------------------------------------------------------------------#
#           make a selection                                                   #
#------------------------------------------------------------------------------#
def select_item(choices):
    char = None
    while True:
        char = getch()
        if int(char) in choices:
            break
    return(char)

#------------------------------------------------------------------------------#
#           select sound card                                                  #
#------------------------------------------------------------------------------#
def select_sound_card():
    choices = {}
    print('Please select sound card type')
    count = 1
    for card in conf['SOUND-CARDS']:
        choices[count] = card
        print(count, card)
        count = count + 1
    selection = choices[int(select_item(choices))]
    for card in conf['SOUND-CARDS']:
        search_string = conf['SOUND-CARDS'][card]['CONFIG-STRING'] + '\n'
        cfg_string = 'dtoverlay=' + search_string
        if card == selection:
            search_and_replace('/tmp/config.txt', search_string, cfg_string, True, False)
            print(cfg_string)
            print('->plugin.conf<-')
            print('MIXER_DEVICE    = hw:' + conf['SOUND-CARDS'][card]['MIXER'])
            print('MIXER_CONTROL   = ' + conf['SOUND-CARDS'][card]['CONTROL'])
            print('->plugin.conf<-')
        else:
            search_and_replace('/tmp/config.txt', search_string, cfg_string, False, True)


conf = read_config('setup.conf')
script_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_path)

if len(sys.argv) > 1:
    if sys.argv[1] == 'getfiles':
        get_files()
        exit(0)

#execute_pre_cmd()
#install_debian_packages()
#install_pip_packages()
#install_manual_packages()
#copy_files()
#fix_hostname()
#execute_post_cmd()
execute_as_pi()
print('Setup of mediamanager done :-)')
print('Please reboot now')
#select_sound_card()
