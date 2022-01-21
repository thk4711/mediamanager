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
from datetime import datetime
import lib.common as common
import pathlib

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
    global config
    script_path = str(pathlib.Path(__file__).parent.absolute())
    config = common.read_config(script_path + '/qt-gui.conf')
    service_list = []
    time.sleep(3)
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
    args = common.init_frontend()
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

#-------------- start thread for watching volume change -----------------------#
def run_control_watch():
    try:
        _thread.start_new_thread( control_watch, () )
    except:
        print("Error: unable to start thread control watch")

#---------- scale a screen coordinate to actual screen dimension --------------#
def scale(what, value):
    if what == 'x':
        return int(value * screen_width / 100)
    if what == 'y':
        return int(value * screen_height / 100)
    return 1

#-------------------- define some GUI elements --------------------------------#

class MyPushButton(QPushButton):
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

class MyQSvgWidget(QtSvg.QSvgWidget):
    pass

#------------------------------------------------------------------------------#
#                       QT based UI                                            #
#------------------------------------------------------------------------------#
class MediaManagerGUI(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    #---------------------- init the UI ---------------------------------------#
    def initUI(self):
        palette = self.palette()
        role = self.backgroundRole()
        palette.setColor(role, QColor('black'))
        self.setPalette(palette)
        cover_size = scale('x', 25)
        self.setMouseTracking(True)
        self.mouseMoveEvent=lambda event:hide_and_show_stuff('switch', 'cursor', 2)
        pixmap_1 = QPixmap('images/pause.png').scaled(cover_size, cover_size, Qt.KeepAspectRatio)
        QFontDatabase.addApplicationFont("fonts/Roboto-Condensed-Light.ttf")
        QFontDatabase.addApplicationFont("fonts/Material-Design-Iconic-Font.ttf")
        QFontDatabase.addApplicationFont("fonts/socialicious.ttf")
        QFontDatabase.addApplicationFont("fonts/CODE_Light.otf")

        #------------------ switch active service -----------------------------#
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

        #----------------- exchange a pixmap at a gui element -----------------#
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
                    new_pixmap = tmp_pic.scaled(cover_size, cover_size, Qt.KeepAspectRatio)
                else:
                    new_pixmap = QPixmap(new_image).scaled(cover_size, cover_size, Qt.KeepAspectRatio)
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

        #--------------- fade out old metadata text ---------------------------#
        def exchange_metadata_text(item, type, new_text):
            self.widget = item
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            gui_amimations[type] = QPropertyAnimation(self.effect, b"opacity")
            gui_amimations[type].setDuration(500)
            gui_amimations[type].setStartValue(1.0)
            gui_amimations[type].setEndValue(0.0)
            gui_amimations[type].finished.connect(lambda: exchange_metadata_text_2(item, type, new_text))
            gui_amimations[type].start()

        #--------------- fade in new metadata text ----------------------------#
        def exchange_metadata_text_2(item, type, new_text):
            self.widget = item
            self.widget.setText(new_text)
            self.effect = QGraphicsOpacityEffect()
            self.widget.setGraphicsEffect(self.effect)
            gui_amimations[type] = QPropertyAnimation(self.effect, b"opacity")
            gui_amimations[type].setDuration(500)
            gui_amimations[type].setStartValue(0.0)
            gui_amimations[type].setEndValue(1.0)
            gui_amimations[type].start()

        #------------ handle play/pause button --------------------------------#
        def play_pause():
            if meta_data['playstatus']:
                gui_objects['playpause']['object'].setText(u'\uF3A7')
                play_status = True
            else:
                gui_objects['playpause']['object'].setText(u'\uF3AA')
                play_status = False
                if service_list[meta_data['service']]['type'] == 'font':
                    symbol = service_list[meta_data['service']]['symbol'].encode().decode('unicode-escape')
                    cover = create_pixmap_from_font(cover_size, cover_size, symbol, int(0.8*cover_size))
                    exchange_pixmap(gui_objects['cover']['object'], cover, True)
                elif service_list[meta_data['service']]['type'] == 'svg':
                    cover = QIcon('frontends/icons/' + service_list[meta_data['service']]['icon1']).pixmap(QSize(cover_size, cover_size))
                    exchange_pixmap(gui_objects['cover']['object'], cover, True)

        #---------------------- update time -----------------------------------#
        def update_time():
            global old_time_string
            now = datetime.now()
            time_string = now.strftime("%H:%M")
            if old_time_string != time_string:
                time_label.setText(time_string)
                old_time_string = time_string

        #------------------ update metadata -----------------------------------#
        def update_metadata():
            global update_count
            update_count = update_count + 1
            get_metadata()
            flag = False
            if update_count < 4:
                self.update()
            if old_meta_data['service'] != meta_data['service']:
                switch_active_service(meta_data['service'])
                flag = True
                old_meta_data['service'] = meta_data['service']

            for item in ['track', 'album', 'artist']:
                if old_meta_data[item] != meta_data[item]:
                    exchange_metadata_text(gui_objects[item + '_label']['object'], item, meta_data[item])
                    old_meta_data[item] = meta_data[item]

            if old_meta_data['cover'] != meta_data['cover']:
                if meta_data['playstatus']:
                    exchange_pixmap(gui_objects['cover']['object'], meta_data['cover'])
                old_meta_data['cover'] = meta_data['cover']

            if old_meta_data['volume'] != meta_data['volume']:
                old_meta_data['volume'] = meta_data['volume']

            if old_meta_data['playstatus'] != meta_data['playstatus'] or flag:
                play_pause()
                old_meta_data['playstatus'] = meta_data['playstatus']

            update_time()

        #--------- create a pixmap from font character ------------------------#
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

        #---------- display volume if changed  --------------------------------#
        def update_volume():
            global oldvol
            hide_and_show_stuff('check','volume')
            hide_and_show_stuff('check','metadata')
            if oldvol != setvol:
                hide_and_show_stuff('switch','metadata')
                hide_and_show_stuff('switch','volume')
                gui_objects['vol_label']['object'].setText(str(setvol))
                oldvol = setvol

        #-----------  hide or show gui elements based on timer  ---------------#
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
                    MediaManager.setOverrideCursor(Qt.ArrowCursor)

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
                    MediaManager.setOverrideCursor(Qt.BlankCursor)

        #----------- switch to other service ----------------------------------#
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

        #------------- create a GUI element -----------------------------------#
        def create_gui_object(name,type,group=None,param_1=None,param_2=None,param_3=None):
            label_size = scale('x',75)
            font_size = scale('y',4)
            icon_size = scale('x',3)

            gui_object = {}

            if type == 'QLabel_bold':
                gui_object['object'] = QLabel_b('')
                gui_object['object'].setMaximumWidth(label_size)
                gui_object['object'].setStyleSheet(f'font-size: {font_size}px;')

            elif type == 'QLabel_normal':
                gui_object['object'] = QLabel('')
                gui_object['object'].setMaximumWidth(label_size)
                gui_object['object'].setStyleSheet(f'font-size: {font_size}px;')

            elif type == 'Push_Button':
                pb_width  = scale('x',6)
                pb_height = scale('x',3)
                pb_font_size = scale('y',4)
                gui_object['object'] = MyPushButton(param_1)
                style = f'font-size: {pb_font_size}px; min-width: {pb_width}px; min-height: {pb_height}px; max-width: {pb_width}px; max-height: {pb_height}px;'
                gui_object['object'].setStyleSheet(style)

            elif type == 'Service_icon_font':
                icon_font_size = scale('y',4.5)
                padding = scale('x',0.3)
                symbol = param_1.encode().decode('unicode-escape')
                gui_objects[name + 'img1'] = {}
                gui_objects[name + 'img1']['object'] = MyQLabelInactive(symbol)
                gui_objects[name + 'img1']['object'].setStyleSheet(f'min-width: {icon_size}px; min-height: {icon_size}px; max-width: {icon_size}px; max-height: {icon_size}px;')
                gui_objects[name + 'img1']['object'].setStyleSheet(f'font-size: {icon_font_size}px; padding-left: {padding}px;')
                gui_objects[name + 'img2'] = {}
                gui_objects[name + 'img2']['object'] = MyQLabelActive(symbol)
                gui_objects[name + 'img2']['object'].setStyleSheet(f'min-width: {icon_size}px; min-height: {icon_size}px; max-width: {icon_size}px; max-height: {icon_size}px;')
                gui_objects[name + 'img2']['object'].setStyleSheet(f'font-size: {icon_font_size}px; padding-left: {padding}px;')
                gui_objects[name + 'img3'] = {}
                gui_objects[name + 'img3']['object'] = MyQLabelActive(' ')
                gui_objects[name + 'img3']['object'].setStyleSheet(f'min-width: {icon_size}px; min-height: {icon_size}px; max-width: {icon_size}px; max-height: {icon_size}px;')
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
                gui_objects[name + 'img1']['object'].setStyleSheet(f'min-width: {icon_size}px; min-height: {icon_size}px; max-width: {icon_size}px; max-height: {icon_size}px;')
                gui_objects[name + 'img2'] = {}
                gui_objects[name + 'img2']['object'] = MyQSvgWidget('frontends/icons/' + param_2)
                gui_objects[name + 'img2']['object'].setStyleSheet(f'min-width: {icon_size}px; min-height: {icon_size}px; max-width: {icon_size}px; max-height: {icon_size}px;')
                gui_objects[name + 'img3'] = {}
                gui_objects[name + 'img3']['object'] = MyQLabelActive(' ')
                gui_objects[name + 'img3']['object'].setStyleSheet(f'min-width: {icon_size}px; min-height: {icon_size}px; max-width: {icon_size}px; max-height: {icon_size}px;')
                gui_object['object'] = MyStack()
                gui_object['object'].addWidget(gui_objects[name + 'img1']['object'])
                gui_object['object'].addWidget(gui_objects[name + 'img2']['object'])
                gui_object['object'].addWidget(gui_objects[name + 'img3']['object'])
                gui_object['object'].setCurrentIndex(0)

            elif type == 'QLabel_cover':
                gui_object['object'] = QLabel('')
                gui_object['object'].setFixedSize(cover_size, cover_size)

            elif type == 'QLabel_volume':
                hight = scale('y',27)
                width = scale('x',26)
                font_size = int(0.9*hight)
                space = int(0.5*width)
                gui_object['object'] = MyQLabelVolume('')
                gui_object['object'].setStyleSheet(f'min-width: {width}px; min-height: {hight}px; max-width: {width}px; max-height: {hight}px; font-size: 290px; margin-left: 250px;')
                gui_object['object'].setStyleSheet(f'font-size: {font_size}px; margin-left: {space}px;')
                gui_object['object'].hide

            gui_object['group'] = group
            gui_object['type'] = type
            gui_object['reset_time'] = 0
            gui_object['reset_needed'] = False
            gui_object['default'] = 'show'
            gui_objects[name] = gui_object

        #------------ create VBox for metadata --------------------------------#
        def setup_metadata_gui_elements():
            vbox_metadata = QVBoxLayout()
            vbox_metadata.setSpacing(0)
            vbox_metadata.addStretch(1)
            create_gui_object('track_label','QLabel_bold','metadata')
            vbox_metadata.addWidget(gui_objects['track_label']['object'])
            create_gui_object('artist_label','QLabel_normal','metadata')
            vbox_metadata.addWidget(gui_objects['artist_label']['object'])
            create_gui_object('album_label','QLabel_normal','metadata')
            vbox_metadata.addWidget(gui_objects['album_label']['object'])
            vbox_metadata.addStretch(1)
            gui_layouts['vbox_metadata'] = vbox_metadata

        #------------- create VBox for service icons --------------------------#
        def setup_service_icon_gui_elements(orientation = 'V'):
            box_service_icons = None
            if orientation == 'V':
                box_service_icons = QVBoxLayout()
                print('creating VBox')
            elif orientation == 'H':
                box_service_icons = QHBoxLayout()
                print('creating HBox')
            box_service_icons.setContentsMargins(20, 0, 0, 0)
            box_service_icons.addStretch(1)
            global service_array
            service_array = []
            count = 0
            for service in service_list:
                service_array.append(service)
                if service_list[service]['type'] == 'font':
                    create_gui_object(service, 'Service_icon_font', 'service_icons', service_list[service]['symbol'])
                elif service_list[service]['type'] == 'svg':
                    create_gui_object(service, 'Service_icon_svg', 'service_icons', service_list[service]['icon1'], service_list[service]['icon2'])
                box_service_icons.addWidget(gui_objects[service]['object'])
                if orientation == 'H':
                    gui_objects[service]['object'].setContentsMargins(20, 0, 20, 0)
                if count == 0: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[0], True))
                if count == 1: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[1], True))
                if count == 2: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[2], True))
                if count == 3: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[3], True))
                if count == 4: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[4], True))
                if count == 5: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[5], True))
                if count == 6: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[6], True))
                if count == 7: gui_objects[service]['object'].clicked.connect(lambda : switch_active_service(service_array[7], True))
                count = count + 1
            box_service_icons.addStretch(1)
            gui_layouts['box_service_icons'] = box_service_icons

        #------------------ create on screen control HBox ---------------------#
        def setup_playback_controls_gui_elements():
            width  = scale('x',6)
            height = scale('x',2)
            space = scale('x',12)
            font_size = scale('y',3)
            box_playback_controls = QHBoxLayout()
            box_playback_controls.setSpacing(space)
            box_playback_controls.setContentsMargins(space, 0, 0, 0)
            create_gui_object('mode','Push_Button','playback_controls', 'Mode')
            gui_objects['mode']['object'].clicked.connect(lambda: common.get_data(host,port,'shift'))
            box_playback_controls.addWidget(gui_objects['mode']['object'])
            create_gui_object('prev','Push_Button','playback_controls', u'\uF3B5')
            gui_objects['prev']['object'].clicked.connect(lambda: common.get_data(host,port,'prev'))
            box_playback_controls.addWidget(gui_objects['prev']['object'])
            create_gui_object('playpause','Push_Button','playback_controls', u'\uF3AA')
            gui_objects['playpause']['object'].clicked.connect(lambda: common.get_data(host,port,'toggle'))
            box_playback_controls.addWidget(gui_objects['playpause']['object'])
            create_gui_object('next','Push_Button','playback_controls', u'\uF3B4')
            gui_objects['next']['object'].clicked.connect(lambda: common.get_data(host,port,'next'))
            box_playback_controls.addWidget(gui_objects['next']['object'])
            box_playback_controls.addStretch(1)
            gui_layouts['box_playback_controls'] = box_playback_controls

        #-------------- create the overall screen layout ----------------------#
        def setup_screen_layout():
            space = scale('x',1.7)
            create_gui_object('cover','QLabel_cover','cover')
            create_gui_object('placeholder','QLabel_cover','cover')
            gui_objects['placeholder']['object'].hide()
            create_gui_object('vol_label','QLabel_volume','volume')
            gui_objects['vol_label']['default'] = 'hide'

            gui_layouts['hbox_middle'] = QHBoxLayout()
            gui_layouts['hbox_middle'].setSpacing(space)
            gui_layouts['hbox_middle'].addWidget(gui_objects['placeholder']['object'])
            gui_layouts['hbox_middle'].addWidget(gui_objects['cover']['object'])
            gui_layouts['hbox_middle'].addLayout(gui_layouts['vbox_metadata'])
            gui_layouts['hbox_middle'].addWidget(gui_objects['vol_label']['object'])
            gui_layouts['hbox_middle'].addStretch(1)

            gui_layouts['vbox_central'] = QVBoxLayout()
            if config['general']['service-button-orientation'] == 'vertical':
                gui_layouts['vbox_central'].addLayout(gui_layouts['box_service_icons'])
            gui_layouts['vbox_central'].addStretch(1)
            gui_layouts['vbox_central'].addLayout(gui_layouts['hbox_middle'])
            gui_layouts['vbox_central'].addStretch(1)
            if config['general']['show-controls'] == True:
                gui_layouts['vbox_central'].addLayout(gui_layouts['box_playback_controls'])

            # main layout
            gui_layouts['all'] = QHBoxLayout()
            if config['general']['service-button-orientation'] == 'horizontal':
                gui_layouts['all'].setSpacing(space)
                gui_layouts['all'].addLayout(gui_layouts['box_service_icons'])
            gui_layouts['all'].addLayout(gui_layouts['vbox_central'])
            if config['general']['service-button-orientation'] == 'horizontal':
                gui_layouts['all'].addStretch(1)

        #---------- do some stuff at the beginning ----------------------------#
        gui_objects = {}
        gui_layouts = {}
        gui_amimations = {}
        sshFile = str(script_path) + "/qt-gui.stylesheet"
        with open(sshFile,"r") as fh:
            self.setStyleSheet(fh.read())

        setup_metadata_gui_elements()
        if config['general']['service-button-orientation'] == 'vertical':
            setup_service_icon_gui_elements('H')
        else:
            setup_service_icon_gui_elements('V')
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

#------------------------------------------------------------------------------#
#                main programm                                                 #
#------------------------------------------------------------------------------#
if __name__ == '__main__':

    os.environ["QT_QPA_PLATFORM"] = "linuxfb"
    os.environ["QT_QPA_EVDEV_KEYBOARD_PARAMETERS"] = "grab=0"
    init()
    MediaManager = QApplication(sys.argv)
    MediaManager.setStyle('Fusion')
    screen_resolution = MediaManager.desktop().screenGeometry()
    screen_width, screen_height = screen_resolution.width(), screen_resolution.height()
    print('geometry:', screen_width, screen_height)
    MediaManager.setOverrideCursor(Qt.BlankCursor)
    MediaManagerGUI()
    sys.exit(MediaManager.exec_())
