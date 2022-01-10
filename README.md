# mediamanager
modular audio software supporting various audio sources and hardware add ons based on Raspberry Pi   

### basic concept
The goal of this project to create audio devices which feel less like a computer - more as an appliance like the ones you can by but with the fredom of an open source software behind. To operate it there is no need for an app on your phome or a touch screen. I started this project to convert an old TEAC fm tuner into a modern day audio device. I did want to preserve the aperance as much as possible. This also gave me simple access to a decent case for my project.

The software consists 3 types of scripts:
#### manager
- This process is managing, which processes will be started and makes sure that these are running all the time.
- It is sending commands like play, pause, next track etc. to the sources like spotify, mpd, usb, etc.
- It is providing status information like metadata and play status.
- It is listening for control inputs from bacends like buttons, remote controlls, touch screens, etc. and routes these commands to the active sound source.

#### services
- Services are the source of sound. These can be streaming services like spotify, internet radio or physical connections like usb, SPDIF or line in.
- Based on the capabilities of a particular service it processes commands like play, pause, next track etc.
- Based on the capabilities of a particular service it is providing metadata like Artist, song etc.

#### frontends
- Frontends are components which users interact with.
- They can display metadata and status information.
- They can trigger actions like play, pause, next track etc. at the active service.

#### hardware library
A device specific hardware library is needed to do certain adjustments like switching GPIO's calling certain commands when there is a switch to an other audio service. It has to be adapted, depending on the device you want to build. If this is not needed in your case it might be just a dummy which is not really doing anything.

### services
Mediamanager rigt now comes with the following services. It is very easy to integrate more services. If you want to know more please have a look at this document.
#### bluetooth-service
This service is using the build in bluetooth module of the raspberry pi to recive audio data. You can pair with this service with every phone , tablet etc. The serice does support metadata and playback controls.
#### generic-service
This service implemets the bare minimum of functionality. It i used for things like SPDIF or line in inputs, which do not provide metadata and allow no further control. This service can be used as a teplate for new developments. Usually additional hardware like i2s switches or AD boards are nesesarry.
#### radio-service
This service is used for playback of internet radio stations. The stations can be configured in the radio-service.conf file. The serice does support metadata and playback controls.
#### shairport-service
This service is using the shaiport software to enable AirPlay on the device. The serice does support metadata and playback controls.
#### spotify-service
This service is using spocon (which is using librespot-java) to implement the spotify connect service. The serice does support metadata and playback controls.
#### usb-service
This service is using an usb sound interface with i2s interface to get the sound into the device. It also requires an i2s switch between the usb interface and the raspberry on one side and the DAC board on the other side. If you want to use playback controls an additional Arduino bord is needed (please see this file for details).

### frontends
Mediamanager rigt now comes with the following services. It is very easy to integrate more frontends. If you want to know more please have a look at this document.
#### display_16x2
This frontend is using 2 16x2 charakter display connected with i2c to display the current volume the time the playback status and the active service.
#### encoder
This frontend is using a rotary encoder to change the volume. If the encoder includes a push button as well it can be configured what this butto does.
#### extra-buttons
This frontend is using free GPIO's to trigger certain playback controls.
#### infrared
This frontend is using lirc to trigger certain controls using an infrared remote control.
#### pcf-buttons
This frontend is using an pcf8575 i2c IO expander chip (16 additional GPIO#s) to trigger controls. This is especially usefull if you want to repurpose an old device and want to be able to use all the existing buttons.
