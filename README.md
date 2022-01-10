# mediamanager
modular audio software supporting various audio sources and hardware add ons based on Raspberry Pi   

### basic concept
The goal of this project to create audio devices which feel less like a computer - more as an appliance like the ones you can by but with the fredom of an open source software behind. To operate it there is no need for an app on your phome or a touch screen. I started this project to convert an old TEAC fm tuner into a modern day audio device. I did want to preserve the aperance as much as possible. This also gave me simple access to a decent case for my project.

The software consists 3 types of scripts:
#### manager<br>
- This process is managing, which processes will be started and makes sure that these are running all the time.
- It is sending commands like play, pause, next track etc. to the sources like spotify, mpd, usb, etc.
- It is providing status information like metadata and play status.
- It is listening for control inputs from bacends like buttons, remote controlls, touch screens, etc. and routes these commands to the active sound source.

#### services<br>
- Services are the source of sound. These can be streaming services like spotify, internet radio or physical connections like usb, SPDIF or line in.
- Based on the capabilities of a particular service it processes commands like play, pause, next track etc.
- Based on the capabilities of a particular service it is providing metadata like Artist, song etc.

#### frontends<br>
- Frontends are components which users interact with.
- They can display metadata and status information.
- They can trigger actions like play, pause, next track etc. at the active service.

