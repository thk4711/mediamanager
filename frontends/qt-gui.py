#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QFrame, QSizePolicy, QStackedWidget, QProgressBar, QHBoxLayout, QVBoxLayout, QGridLayout, QStackedLayout, QApplication, QScrollBar, QSlider, QGraphicsOpacityEffect
from PyQt5.QtCore import QTimer, QSize, QPropertyAnimation, Qt, pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QPalette, QColor, QPixmap, QFontDatabase, QPainter, QFont, QIcon
from PyQt5 import QtSvg
import urllib.request
import time
import json
import socket
import alsaaudio
import select
import _thread
import os
import argparse
from datetime import datetime
import lib.common as common
import pathlib
import pprint

meta_data = {}
old_meta_data = {}
play_status = False
old_slider_update_time = 0
setvol = 0
oldvol = 0
update_count = 0
vol_number_reset_time = 0
vol_number_reset_neded = False

cursor_show = False
cursore_reset_time = 0

def init():
    global meta_data
    global old_meta_data
    global mixer
    global setvol
    global port
    global host
    global old_time_string
    global service_list
    global script_path
    script_path = pathlib.Path(__file__).parent.absolute()
    service_list = []
    old_time_string = '00:00'
    meta_data['track']  = " "
    meta_data['album']  = " "
    meta_data['artist'] = " "
    meta_data['cover']  = "images/pause.png"
    meta_data['playstatus']  = False
    meta_data['service']  = 'radio'
    meta_data['volume'] = setvol
    old_meta_data['track']  = "  "
    old_meta_data['album']  = "  "
    old_meta_data['artist'] = "  "
    old_meta_data['cover']  = "  "
    old_meta_data['playstatus']  = True
    old_meta_data['service']  = ''
    old_meta_data['volume'] = 1
    parser = argparse.ArgumentParser(description='media helper')
    parser.add_argument('-p', '--port', type=int, help='manager port', required=True)
    parser.add_argument('-ho', '--host', type=str, help='manager host', required=False, default='localhost')
    parser.add_argument('-m', '--mixer', type=str, help='volume mixer name', required=True)
    args = parser.parse_args()
    port = args.port
    host = args.host
    mixer_name = args.mixer
    mixer = alsaaudio.Mixer(mixer_name)
    alsa_val = mixer.getvolume()
    value = alsa_val[0]
    setvol = value
    str_data = common.get_data(host,port,'getservicelist')
    service_list = json.loads(str_data.decode('utf-8'))
    run_control_watch()


#------------------------------------------------------------------------------#
#        get metadata from mpd                                                 #
#------------------------------------------------------------------------------#
def get_metadata():
    global meta_data
    global play_status
    str_data = common.get_data(host,port,'metadata')
    data = json.loads(str_data.decode('utf-8'))
    meta_data['track']  = data['track']
    meta_data['album']  = data['album']
    meta_data['artist'] = data['artist']
    meta_data['cover']  = data['cover']
    meta_data['playstatus']  = data['playstatus']
    meta_data['service']  = data['service']

#---------------------- watch control changes ---------------------------------#
def control_watch():
    global controls
    global setvol
    poll = select.poll()
    descriptors = mixer.polldescriptors()
    poll.register(descriptors[0][0])
    while True:
        events = poll.poll()
        mixer.handleevents()
        for e in events:
            alsa_val = mixer.getvolume()
            value = alsa_val[0]
            setvol = value

#--------- start thread for watching volume change ----------------------------#
def run_control_watch():
    try:
        _thread.start_new_thread( control_watch, () )
    except:
        print("Error: unable to start thread control watch")


class MyPushButton(QPushButton):
    pass

class My2ndPushButton(QPushButton):
    pass

class MyServiceButton(QPushButton):
    pass

class MyServiceButtonActive(QPushButton):
    pass

class MyServiceButtonInactive(QPushButton):
    pass

class MySlider(QSlider):
    pass

class VSlider(QSlider):
    pass

class QLabel_b(QLabel):
    pass

class MyQLabelActive(QLabel):
    pass

class MyQLabelInactive(QLabel):
    pass

class MyQLabelVolume(QLabel):
    pass

class MyStack(QStackedWidget):
    clicked=pyqtSignal()
    def mousePressEvent(self, ev):
        self.clicked.emit()

class MyQWidget(QWidget):
    pass

class MyQSvgWidget(QtSvg.QSvgWidget):
    pass

class Example(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        palette = self.palette()
        role = self.backgroundRole()
        palette.setColor(role, QColor('black'))
        self.setPalette(palette)
        self.setGeometry(1280, 800, 1280, 800)
        self.setMouseTracking(True)
        self.mouseMoveEvent=lambda event:hide_and_show_stuff('switch', 'cursor', 2)
        pixmap_1 = QPixmap('images/pause.png').scaled(400, 400, Qt.KeepAspectRatio)
        QFontDatabase.addApplicationFont("fonts/Roboto-Condensed-Light.ttf")
        QFontDatabase.addApplicationFont("fonts/Material-Design-Iconic-Font.ttf")
        QFontDatabase.addApplicationFont("fonts/socialicious.ttf")
        QFontDatabase.addApplicationFont("fonts/CODE_Light.otf")

    #---------------------- switch active service ---------------------------------#

        def exchange_pixmap(item, new_image, is_pixmap = False):
            self.widget = item
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim = QPropertyAnimation(self.effect, b"opacity")
            self.anim.setDuration(500)
            self.anim.setStartValue(1.0)
            self.anim.setEndValue(0.0)
            self.anim.finished.connect(lambda: exchange_pixmap_2(item, new_image, is_pixmap))
            self.anim.start()

        def exchange_pixmap_2(item, new_image, is_pixmap):
            self.widget = item
            new_pixmap = QPixmap()
            tmp_pic = QPixmap()
            if is_pixmap:
                new_pixmap = new_image
            else:
                if 'external_' in new_image:
                    data = common.get_data(host,port,'coverimage/cover=' + new_image)
                    tmp_pic.loadFromData(data)
                    new_pixmap = tmp_pic.scaled(400, 400, Qt.KeepAspectRatio)
                else:
                    new_pixmap = QPixmap(new_image).scaled(400, 400, Qt.KeepAspectRatio)
            if meta_data['playstatus']:
                gui_objects['placeholder']['object'].hide()
            else:
                gui_objects['placeholder']['object'].show()
            self.widget.setPixmap(new_pixmap)
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim = QPropertyAnimation(self.effect, b"opacity")
            self.anim.setDuration(500)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()

        def exchange_artist_text(item, new_text):
            self.widget = item
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim1 = QPropertyAnimation(self.effect, b"opacity")
            self.anim1.setDuration(500)
            self.anim1.setStartValue(1.0)
            self.anim1.setEndValue(0.0)
            self.anim1.finished.connect(lambda: exchange_artist_text_2(item, new_text))
            self.anim1.start()

        def exchange_artist_text_2(item, new_text):
            self.widget = item
            self.widget.setText(new_text)
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim1 = QPropertyAnimation(self.effect, b"opacity")
            self.anim1.setDuration(500)
            self.anim1.setStartValue(0.0)
            self.anim1.setEndValue(1.0)
            self.anim1.start()

        def exchange_album_text(item, new_text):
            self.widget = item
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim2 = QPropertyAnimation(self.effect, b"opacity")
            self.anim2.setDuration(500)
            self.anim2.setStartValue(1.0)
            self.anim2.setEndValue(0.0)
            self.anim2.finished.connect(lambda: exchange_album_text_2(item, new_text))
            self.anim2.start()

        def exchange_album_text_2(item, new_text):
            self.widget = item
            self.widget.setText(new_text)
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim2 = QPropertyAnimation(self.effect, b"opacity")
            self.anim2.setDuration(500)
            self.anim2.setStartValue(0.0)
            self.anim2.setEndValue(1.0)
            self.anim2.start()

        def exchange_title_text(item, new_text):
            self.widget = item
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim3 = QPropertyAnimation(self.effect, b"opacity")
            self.anim3.setDuration(500)
            self.anim3.setStartValue(1.0)
            self.anim3.setEndValue(0.0)
            self.anim3.finished.connect(lambda: exchange_title_text_2(item, new_text))
            self.anim3.start()

        def exchange_title_text_2(item, new_text):
            self.widget = item
            self.widget.setText(new_text)
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            self.anim3 = QPropertyAnimation(self.effect, b"opacity")
            self.anim3.setDuration(500)
            self.anim3.setStartValue(0.0)
            self.anim3.setEndValue(1.0)
            self.anim3.start()

        def play_pause():
            global play_status
            if play_status:
                gui_objects['playpause']['object'].setText(u'\uF3AA')
                play_status = False
                common.get_data(host,port,'pause')
            else:
                gui_objects['playpause']['object'].setText(u'\uF3A7')
                play_status = True
                common.get_data(host,port,'play')

        def update_metadata():
            global update_count
            global old_time_string
            update_count = update_count + 1
            get_metadata()
            flag = False
            if update_count < 4:
                self.update()
            if old_meta_data['service'] != meta_data['service']:
                switch_active_service(meta_data['service'])
                flag = True
                old_meta_data['service'] = meta_data['service']
            if old_meta_data['track'] != meta_data['track']:
                #title_label.setText(meta_data['track'])
                exchange_title_text(gui_objects['title_label']['object'],meta_data['track'])
                old_meta_data['track'] = meta_data['track']
            if old_meta_data['album'] != meta_data['album']:
                #album_label.setText(meta_data['album'])
                exchange_album_text(gui_objects['album_label']['object'],meta_data['album'])
                old_meta_data['album'] = meta_data['album']
            if old_meta_data['artist'] != meta_data['artist']:
                #artist_label.setText(meta_data['artist'])
                exchange_artist_text(gui_objects['artist_label']['object'],meta_data['artist'])
                old_meta_data['artist'] = meta_data['artist']
            if old_meta_data['cover'] != meta_data['cover']:
                if meta_data['playstatus']:
                    exchange_pixmap(gui_objects['cover']['object'], meta_data['cover'])
                old_meta_data['cover'] = meta_data['cover']
            if old_meta_data['volume'] != meta_data['volume']:
                old_meta_data['volume'] = meta_data['volume']
            if old_meta_data['playstatus'] != meta_data['playstatus'] or flag:
                if meta_data['playstatus']:
                    gui_objects['playpause']['object'].setText(u'\uF3A7')
                    play_status = True
                else:
                    gui_objects['playpause']['object'].setText(u'\uF3AA')
                    play_status = False
                    if service_list[meta_data['service']]['type'] == 'font':
                        symbol = service_list[meta_data['service']]['symbol'].encode().decode('unicode-escape')
                        cover = create_pixmap_from_font(400, 400, symbol, 250)
                        exchange_pixmap(gui_objects['cover']['object'], cover, True)
                    elif service_list[meta_data['service']]['type'] == 'svg':
                        cover = QIcon('frontends/icons/' + service_list[meta_data['service']]['icon1']).pixmap(QSize(350, 350))
                        exchange_pixmap(gui_objects['cover']['object'], cover, True)
                old_meta_data['playstatus'] = meta_data['playstatus']
            now = datetime.now()
            time_string = now.strftime("%H:%M")
            if old_time_string != time_string:
                time_label.setText(time_string)
                old_time_string = time_string

        def create_pixmap_from_font(size_x, size_y, text, font_size):
            pixmap = QPixmap(size_x, size_y)
            pixmap.fill(QColor("black"))
            painter = QPainter()
            painter.begin(pixmap)
            painter.setPen(QColor(160, 160, 160))
            painter.setFont(QFont("Material-Design-Iconic-Font", font_size))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
            painter.end()
            return(pixmap)

        def update_volume():
            global oldvol
            hide_and_show_stuff('check','volume')
            hide_and_show_stuff('check','metadata')
            if oldvol != setvol:
                hide_and_show_stuff('switch','metadata')
                hide_and_show_stuff('switch','volume')
                gui_objects['vol_label']['object'].setText(str(setvol))
                oldvol = setvol

        def hide_and_show_stuff(action, group=None, timeout=2.5):
            global cursor_show
            global cursore_reset_time
            if action == 'switch':
                for item in gui_objects:
                    if 'group' in gui_objects[item]:
                        if gui_objects[item]['group'] == group:
                            gui_objects[item]['reset_time'] = time.time() + timeout
                            gui_objects[item]['reset_needed'] = True
                            if gui_objects[item]['default'] == 'show':
                                gui_objects[item]['object'].hide()
                            else:
                                gui_objects[item]['object'].show()
                if group == 'cursor':
                    cursor_show = True
                    cursore_reset_time = time.time() + timeout
                    app.setOverrideCursor(Qt.ArrowCursor)

            if action == 'check':
                for item in gui_objects:
                    if 'group' in gui_objects[item]:
                        if gui_objects[item]['group'] == group:
                            if gui_objects[item]['reset_needed'] and time.time() > gui_objects[item]['reset_time']:
                                gui_objects[item]['reset_needed'] = False
                                if gui_objects[item]['default'] == 'show':
                                    gui_objects[item]['object'].show()
                                else:
                                    gui_objects[item]['object'].hide()
                if cursor_show and time.time() > cursore_reset_time:
                    cursor_show = False
                    app.setOverrideCursor(Qt.BlankCursor)

        gui_objects = {}
        gui_layouts = {}
        sshFile = str(script_path) + "/qt-gui.stylesheet"
        with open(sshFile,"r") as fh:
            self.setStyleSheet(fh.read())

        def switch_active_service(new_service, transmit=False):
            global play_status
            for service in service_list:
                if service == new_service:
                    gui_objects[service]['object'].setCurrentIndex(1)
                else:
                    gui_objects[service]['object'].setCurrentIndex(0)
            if transmit:
                common.get_data(host,port,'switchservice/service=' + new_service)
            result = common.get_data(host,port,'getplaystatus').decode("utf-8")
            if result == 'YES':
                gui_objects['playpause']['object'].setText(u'\uF3A7')
                play_status = True
            else:
                gui_objects['playpause']['object'].setText(u'\uF3AA')
                play_status = False

        def create_gui_object(name,type,group=None,param_1=None,param_2=None,param_3=None):
            label_size = 1500
            gui_object = {}

            if type == 'QLabel_bold':
                gui_object['object'] = QLabel_b('')
                gui_object['object'].setMaximumWidth(label_size)

            elif type == 'QLabel_normal':
                gui_object['object'] = QLabel('')
                gui_object['object'].setMaximumWidth(label_size)

            elif type == 'Volume_label':
                gui_object['object'] = MyQLabelVolume('')
                gui_object['object'].hide()

            elif type == 'Push_Button':
                gui_object['object'] = MyPushButton(param_1)

            elif type == 'Service_icon_font':
                symbol = param_1.encode().decode('unicode-escape')
                gui_objects[name + 'img1'] = {}
                gui_objects[name + 'img1']['object'] = MyQLabelInactive(symbol)
                gui_objects[name + 'img2'] = {}
                gui_objects[name + 'img2']['object'] = MyQLabelActive(symbol)
                gui_objects[name + 'img3'] = {}
                gui_objects[name + 'img3']['object'] = MyQLabelActive(' ')
                gui_object['object'] = MyStack()
                gui_object['object'].addWidget(gui_objects[name + 'img1']['object'])
                gui_object['object'].addWidget(gui_objects[name + 'img2']['object'])
                gui_object['object'].addWidget(gui_objects[name + 'img3']['object'])
                if param_3 != None:
                    gui_object['object'].setContentsMargins(param_3, 0, 0, 0)
                gui_object['object'].setCurrentIndex(0)

            elif type == 'Service_icon_svg':
                gui_objects[name + 'img1'] = {}
                gui_objects[name + 'img1']['object'] = MyQSvgWidget('frontends/icons/' + param_1)
                gui_objects[name + 'img2'] = {}
                gui_objects[name + 'img2']['object'] = MyQSvgWidget('frontends/icons/' + param_2)
                gui_objects[name + 'img3'] = {}
                gui_objects[name + 'img3']['object'] = MyQLabelActive(' ')
                gui_object['object'] = MyStack()
                gui_object['object'].addWidget(gui_objects[name + 'img1']['object'])
                gui_object['object'].addWidget(gui_objects[name + 'img2']['object'])
                gui_object['object'].addWidget(gui_objects[name + 'img3']['object'])
                gui_object['object'].setCurrentIndex(0)

            elif type == 'QLabel_cover':
                gui_object['object'] = QLabel('')
                gui_object['object'].setFixedSize(400, 400)

            elif type == 'QLabel_volume':
                gui_object['object'] = MyQLabelVolume('')
                gui_object['object'].hide

            gui_object['group'] = group
            gui_object['type'] = type
            gui_object['reset_time'] = 0
            gui_object['reset_needed'] = False
            gui_object['default'] = 'show'
            gui_objects[name] = gui_object

        def setup_metadata_gui_elements():
            vbox_metadata = QVBoxLayout()
            vbox_metadata.setSpacing(0)
            vbox_metadata.addStretch(1)
            create_gui_object('title_label','QLabel_bold','metadata')
            vbox_metadata.addWidget(gui_objects['title_label']['object'])
            create_gui_object('artist_label','QLabel_normal','metadata')
            vbox_metadata.addWidget(gui_objects['artist_label']['object'])
            create_gui_object('album_label','QLabel_normal','metadata')
            vbox_metadata.addWidget(gui_objects['album_label']['object'])
            vbox_metadata.addStretch(1)
            gui_layouts['vbox_metadata'] = vbox_metadata

        def setup_service_icon_gui_elements():
            vbox_service_icons = QVBoxLayout()
            vbox_service_icons.setContentsMargins(20, 0, 0, 0)
            vbox_service_icons.addStretch(1)
            global service_array
            service_array = []
            count = 0
            for service in service_list:
                service_array.append(service)
                if service_list[service]['type'] == 'font':
                    create_gui_object(service, 'Service_icon_font', 'service_icons', service_list[service]['symbol'])
                elif service_list[service]['type'] == 'svg':
                    create_gui_object(service, 'Service_icon_svg', 'service_icons', service_list[service]['icon1'], service_list[service]['icon2'])
                vbox_service_icons.addWidget(gui_objects[service]['object'])
                if count == 0: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[0], True))
                if count == 1: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[1], True))
                if count == 2: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[2], True))
                if count == 3: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[3], True))
                if count == 4: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[4], True))
                if count == 5: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[5], True))
                if count == 6: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[6], True))
                if count == 7: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[7], True))
                count = count + 1
            vbox_service_icons.addStretch(1)
            gui_layouts['vbox_service_icons'] = vbox_service_icons

        def setup_playback_controls_gui_elements():
            hbox_playback_controls = QHBoxLayout()
            hbox_playback_controls.setSpacing(263)
            hbox_playback_controls.setContentsMargins(210, 0, 0, 0)
            create_gui_object('mode','Push_Button','playback_controls', 'Mode')
            gui_objects['mode']['object'].clicked.connect(lambda: common.get_data(host,port,'shift'))
            hbox_playback_controls.addWidget(gui_objects['mode']['object'])
            create_gui_object('prev','Push_Button','playback_controls', u'\uF3B5')
            gui_objects['prev']['object'].clicked.connect(lambda: common.get_data(host,port,'prev'))
            hbox_playback_controls.addWidget(gui_objects['prev']['object'])
            create_gui_object('playpause','Push_Button','playback_controls', u'\uF3AA')
            gui_objects['playpause']['object'].clicked.connect(play_pause)
            hbox_playback_controls.addWidget(gui_objects['playpause']['object'])
            create_gui_object('next','Push_Button','playback_controls', u'\uF3B4')
            gui_objects['next']['object'].clicked.connect(lambda: common.get_data(host,port,'next'))
            hbox_playback_controls.addWidget(gui_objects['next']['object'])
            hbox_playback_controls.addStretch(1)
            gui_layouts['hbox_playback_controls'] = hbox_playback_controls

        def setup_screen_layout():
            create_gui_object('cover','QLabel_cover','cover')
            create_gui_object('placeholder','QLabel_cover','cover')
            gui_objects['placeholder']['object'].hide()
            create_gui_object('vol_label','QLabel_volume','volume')
            gui_objects['vol_label']['default'] = 'hide'

            gui_layouts['hbox_middle'] = QHBoxLayout()
            gui_layouts['hbox_middle'].addWidget(gui_objects['placeholder']['object'])
            gui_layouts['hbox_middle'].addWidget(gui_objects['cover']['object'])
            gui_layouts['hbox_middle'].addLayout(gui_layouts['vbox_metadata'])
            gui_layouts['hbox_middle'].addWidget(gui_objects['vol_label']['object'])
            gui_layouts['hbox_middle'].addStretch(1)

            gui_layouts['vbox_central'] = QVBoxLayout()
            gui_layouts['vbox_central'].addStretch(1)
            gui_layouts['vbox_central'].addLayout(gui_layouts['hbox_middle'])
            gui_layouts['vbox_central'].addStretch(1)
            gui_layouts['vbox_central'].addLayout(gui_layouts['hbox_playback_controls'])

            # main layout
            gui_layouts['all'] = QHBoxLayout()
            gui_layouts['all'].addLayout(gui_layouts['vbox_service_icons'])
            gui_layouts['all'].addLayout(gui_layouts['vbox_central'])
            gui_layouts['all'].addStretch(1)

        setup_metadata_gui_elements()
        setup_service_icon_gui_elements()
        setup_playback_controls_gui_elements()
        setup_screen_layout()

        top_middle = QHBoxLayout()
        time_label = QLabel('00:00')
        top_middle.addStretch(1)
        top_middle.addWidget(time_label)
        top_middle.addStretch(1)

        self.setLayout(gui_layouts['all'])
        self.timer = QTimer()
        self.timer.timeout.connect(update_metadata)
        self.timer.start(2000)

        self.timer2 = QTimer()
        self.timer2.timeout.connect(update_volume)
        self.timer2.start(20)
        self.show()


if __name__ == '__main__':

    os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_EVDEV_KEYBOARD_PARAMETERS"] = "grab=0"
    init()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setOverrideCursor(Qt.BlankCursor)
    ex = Example()
    sys.exit(app.exec_())
