#!/bin/sh
echo Starting media manager setup
echo This will take up to 25min
apt -y install git
mkdir /install
cd /install
git clone https://github.com/thk4711/mediamanager
ln -s mediamanager/ manager
cd mediamanager/installer/
./install_prerequisite.py
echo 
echo #--------------------------------#
echo #                                #
echo #    Please reboot now !!!       #
echo #                                #
echo #--------------------------------#

