""" Support for Rotel amplifier which can be remote controlled by serial RS232 port """
import logging
import asyncio
import serial_asyncio
import voluptuous as vol
import traceback
from datetime import timedelta
from functools import partial
from homeassistant.components.media_player import MediaPlayerDevice, PLATFORM_SCHEMA
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.media_player.const import (
    SUPPORT_TURN_ON, 
    SUPPORT_TURN_OFF,
    SUPPORT_VOLUME_SET, 
    SUPPORT_VOLUME_MUTE, 
    SUPPORT_VOLUME_STEP,
    SUPPORT_SELECT_SOURCE,
)

from homeassistant.const import (
    CONF_HOST, 
    CONF_NAME, 
    CONF_PORT, 
    STATE_OFF, 
    STATE_ON, 
    STATE_UNKNOWN, 
    EVENT_HOMEASSISTANT_STOP,
)

import homeassistant.helpers.config_validation as cv

from .roteldataparser import RotelDataParser 

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'ROTEL'
DEFAULT_SOURCE = 'opt1'
CONF_SOURCE = 'source'
CONF_SERIAL_PORT = 'serial_port'

SUPPORT_ROTEL = ( SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_STEP ) 

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SERIAL_PORT): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SOURCE, default=DEFAULT_SOURCE): cv.string,
    }
)

AUDIO_SOURCES = {'phono':'Phono', 'cd':'CD', 'tuner':'Tuner', 'usb':'USB',
                 'opt1':'Optical 1', 'opt2':'Optical 2', 'coax1':'Coax 1', 'coax2':'Coax 2',
                 'bluetooth':'Bluetooth', 'aux1':'Aux 1', 'aux2':'Aux 2'}

AUDIO_SOURCES_SELECT = {'Phono':'phono!', 'CD':'cd!', 'Tuner':'tuner!', 'USB':'usb!',
                 'Optical 1':'opt1!', 'Optical 2':'opt2!', 'Coax 1':'coax1!', 'Coax 2':'coax2!',
                 'Bluetooth':'bluetooth!', 'Aux 1':'aux1!', 'Aux 2':'aux2!'}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """
    Setup the Rotel platform, and the related transport
    Ask for async link as soon as transport is ready
    """
    _LOGGER.info('ROTEL : starting')

    name = config.get(CONF_NAME)
    serial_port = config.get(CONF_SERIAL_PORT)

    rotel = RotelDevice(name, serial_port)    

    async_add_entities([rotel], True)

    async_track_time_interval( hass, rotel.periodic, timedelta(minutes=1) )

    coro = serial_asyncio.create_serial_connection(hass.loop, RotelProtocol, serial_port, baudrate=115200)
    futur = asyncio.run_coroutine_threadsafe(coro, hass.loop)
    futur.add_done_callback(partial(bind_transport_to_device, rotel))

def bind_transport_to_device(device, protocol_refs):
    """
    Bind device and protocol / transport once they are ready
    Update the device status @ start
    """
    transport = protocol_refs.result()[0]
    protocol = protocol_refs.result()[1]
    
    protocol.device = device
    device.transport = transport
    device.send_request('get_current_power!')
    device.send_request('get_volume!')
    device.send_request('get_current_source!')
    device.send_request('get_current_freq!')

class RotelDevice(MediaPlayerDevice):
    """Representation of the Rotel amplifier."""

    def __init__(self, name, serial_port):
        """Initialize the amplifier."""
        _LOGGER.info("ROTEL : initializing")
        self._name = name
        self._media_image_url = "https://www.hifigear.co.uk/media/catalog/product/cache/1/image/800x/602f0fa2c1f0d1ba5e241f914e856ff9/a/1/a12_silver_4.jpg" 
        self._serial_port = serial_port
        self._serial_loop_task = None
        self._state = None
        self._mute = None
        self._volume = '0' 
        self._source = 'phono'
        self._freq = ''
        self._display = ''
        self._attributes = []
        self._rotelDataParser = RotelDataParser()
        _LOGGER.info("ROTEL : RotelDevice initialized")

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        _LOGGER.info("async_added_to_hass")

    def periodic(self, now=None):
        pass
        #self.send_request('get_current_power!')
        #self.send_request('get_volume!')
        #self.send_request('get_current_source!')
        #self.send_request('get_current_freq!')

    @property
    def name(self):
        return self._name

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._media_image_url

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def volume_level(self):
        return int(self._volume) / 100
    
    @property
    def state(self):
        if self._state == 'standby':
            return STATE_OFF
        elif self._state == 'on':
            return STATE_ON
        else:
            return STATE_UNKNOWN

    @property
    def device_state_attributes(self):
        """Return the attributes of the entity (if any JSON present)."""
        return self._attributes

    @property
    def is_volume_muted(self):
        if self._mute == 'on':
            return True
        else:
            return False
   
    @property
    def supported_features(self):
        return SUPPORT_ROTEL

    @property
    def media_title(self):
        if self._source in ('opt1', 'opt2'):
            return '%s 🔊  %s @ %s' % (self._volume, AUDIO_SOURCES[self._source], self._freq)
        else:
            return '%s 🔊  %s' % (self._volume, AUDIO_SOURCES[self._source])

    @property
    def source_list(self):
        return list(AUDIO_SOURCES.values())
   
    @property
    def source(self):
        return AUDIO_SOURCES[self._source]

    def select_source(self, source):
        self.send_request('%s' % AUDIO_SOURCES_SELECT[source])

    def set_volume_level(self, volume):
        self.send_request('volume_%s!' % str(round(volume * 100)).zfill(2))

    def volume_up(self):
        self.send_request('volume_up!')

    def volume_down(self):
        self.send_request('volume_down!')

    def mute_volume(self, mute):
        self.send_request('mute!')

    def turn_on(self):
        self.send_request('power_on!')

    def turn_off(self):
        self.send_request('power_off!')

    def data_received(self, data):
        _LOGGER.info('DEVICE : ROTEL Data received: {!r}'.format(data.decode()))

        self._rotelDataParser.handleParsedData(str(data.decode()))
        cmd = self._rotelDataParser.getNextRotelData()
        if cmd is None:
                _LOGGER.info('DEVICE : No command')
                return
        _LOGGER.info('DEVICE : command:  {!r} '.format(cmd[0]))
        _LOGGER.info('DEVICE : result:  {!r} '.format(cmd[1]))

        while cmd is not None:
            action = cmd[0]
            result = cmd[1] 
            if action == 'volume':
                self._volume = result
            elif action == 'power':
                if result == 'on/standby':
                    self.send_request('get_power!')
                else:
                    self._state = result
            elif action == 'mute':
                if result == 'on/off':
                    self.send_request('get_volume!')
                else:
                    self._mute = result
            elif action == 'source':
                self._source = result
            elif action == 'freq':
                self._freq = result
            elif action == 'display':
                self._desplay = result

            cmd = self._rotelDataParser.getNextRotelData()
        
        self.async_schedule_update_ha_state()

    def send_request(self, message):
        """
        Send messages to the amp (which is a bit cheeky and may need a hard reset if command
        was not properly formatted
        """
        try:
            self.transport.write(message.encode())
            _LOGGER.info('ROTEL Data sent: {!r}'.format(message))
        except:
            _LOGGER.info('ROTEL : transport not ready !')

class RotelProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        _LOGGER.info('ROTEL Transport initialized')

    def data_received(self, data):
        try:
            self.device.data_received(data)
        except Exception as ex:
             traceback.print_exc()
        except:
            _LOGGER.info('ROTEL Data received but not ready {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        _LOGGER.info('ROTEL Connection Lost !')        
