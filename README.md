# Introduction
This is an integration for Home Assistant to allow a Rotel amplifier
be controlled by Home Assistant using it's RS232 interface.
It will let you turn it on and off, adjust the volume and change source.

I use this together with my Rotel RA-12 amplifier and Home Assistant 0.103.5

This is by now a quite old version of HA and I can't say whether it works with 
newer versions of Home Assistant.

# How to use
Add the integration in the Home Assistant custom_components directory.

To configure, I added a configuration like below in configuration.yaml

Adjust to correspond with your RS232 device:


    media_player:
      - platform: rotelserial
        name: ROTEL
        serial_port: /dev/ttyUSB0