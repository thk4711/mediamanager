#!/bin/sh
echo '#--------------------------------#'
echo '#                                #'
echo '# Starting media manager setup   #'
echo '# This will take up to 25min.    #'
echo '#                                #'
echo '#--------------------------------#'
echo ' '
sleep 5
echo This will take up to 25min
apt -y install git
cd /opt
git clone https://github.com/thk4711/mediamanager
cd mediamanager/installer/
./install_prerequisite.py
echo ' '
echo '#--------------------------------#'
echo '#                                #'
echo '#    Please reboot now !!!       #'
echo '#                                #'
echo '#--------------------------------#'
