import logging
import importlib
import socket

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.dpt import DPTBinary
from xknx.telegram import AddressFilter, GroupAddressType
from xknx.tools import group_value_write

XKNX_DPT_MODULE_STR = "xknx.dpt"


class KnxAdapter:

    def __init__(self, config: dict):
        self._config = config

        self.log = logging.getLogger(__name__)

        # Configure group address filters
        self._address_filters = list()
        self._subscription_filters = list()
        for sensor in self._config['sensors']:
            if not ('expose' in sensor and sensor['expose']):
                self._address_filters.append(AddressFilter(sensor['address']))
            if ('expose' in sensor and sensor['expose']) or ('subscribe' in sensor and sensor['subscribe']):
                self._subscription_filters.append(sensor['address'])
        for switch in self._config['switches']:
            if not ('expose' in switch and switch['expose']):
                self._address_filters.append(AddressFilter(switch['address']))
            if ('expose' in switch and switch['expose']) or ('subscribe' in switch and switch['subscribe']):
                self._subscription_filters.append(switch['address'])

    async def run(self):
        try:
            self.log.info("Starting XKNX daemon...")
            await self._xknx.start()
        finally:
            self.log.info("Stopping XKNX daemon...")
            await self._xknx.stop()

    def init(self):
        """Create XKNX object with user configuration"""
        # Step 1: Prepare XKNX configuration structure

        ## General configuration for XKNX
        gen_config = {}
        if 'general' in self._config:
            gen_config = self._config['general']
            if 'address_format' in gen_config:
                addr_format_str = str(gen_config['address_format']).upper()
                gen_config['address_format'] = GroupAddressType[addr_format_str]
                logging.debug("KNX address format is {0}".format(gen_config['address_format']))			

        ## Connection configuation for XKNX
        conn_type = ConnectionType.AUTOMATIC
        conn_params = {}
        if 'connection' in self._config:
            if 'routing' in self._config['connection']:
                conn_type = ConnectionType.ROUTING
                conn_params = self._config['connection']['routing']
            elif 'tunneling' in self._config['connection']:
                conn_type = ConnectionType.TUNNELING
                conn_params = self._config['connection']['tunneling']

                # Resolve gateway ip, if needed
                conn_params['gateway_ip'] = socket.gethostbyname(conn_params['gateway_ip'])

        ## Create XKNX Configuration object
        conn_config = ConnectionConfig(**conn_params, connection_type=conn_type)
        self.log.debug("KNX connection type is {0}".format(conn_type))

        # Step 2: Create XKNX object with configuration
        self._xknx = XKNX(**gen_config, daemon_mode=True, connection_config=conn_config)
        self.log.info("XKNX instance (version %s) for connection to KNX gateway %s created. KNX address of this instance is %s." % (self._xknx.version, conn_config.gateway_ip, self._xknx.current_address))

    def set_telegram_cb(self, cb):
        self._xknx.telegram_queue.register_telegram_received_cb(cb, self._address_filters)

    def get_subscriptions(self):
        return self._subscription_filters

    def find_dpt_type(self, group_address):
        self.log.debug("Try to get dtype for group address {0}".format(group_address))

        dpttype = next((sensor['type'] for sensor in self._config['sensors'] if sensor['address'] == group_address), None)
        if not dpttype:
            dpttype = next((switch['type'] for switch in self._config['switches'] if switch['address'] == group_address), None)
        return dpttype

    def extract_value_from_telegram(self, group_address, telegram):
            dpt_type = self.find_dpt_type(group_address)
            payload = telegram.payload
            value = None
    
            self.log.debug(f"Address: {group_address}, DPT Type: {dpt_type}, Payload: {payload}")
    
            try:
                if dpt_type == 'DPTBinary':
                    value = int(bool(payload.value.value))
                else:
                    if dpt_type is None:
                        dpt_type = payload.value.__class__.__name__
                        self.log.warning(f"No DPTType found for address {group_address}. Using generic type: {dpt_type}.")
                    dpt_class = getattr(importlib.import_module(XKNX_DPT_MODULE_STR), dpt_type)
                    value = dpt_class.from_knx(payload.value)
            except Exception as e:
                self.log.error(e)
    
            return value

    def create_dpt_value(self, group_address, raw_value) -> tuple:
        """Create and return KNX value and type"""
        dpt_type = self.find_dpt_type(group_address)
        self.log.info(f"Address: {group_address}, DPT Type: {dpt_type}, Value: {raw_value}")

        dpt_value = None
        try:
            if dpt_type == 'DPTBinary':
                dpt_value = DPTBinary(int(str(raw_value).lower() in ['true', '1', 'on', 'yes']))
            else:
                dpt_class = getattr(importlib.import_module(XKNX_DPT_MODULE_STR), dpt_type)
                dpt_value = dpt_class.to_knx(raw_value)
        except Exception as e:
            self.log.error(e)

        return dpt_value, dpt_type


    async def publish(self, group_address, value, value_type = None):
        if self._xknx.started:
            group_value_write(self._xknx, group_address, value, value_type)
            self.log.debug(f"Published telegram to group address {group_address} with payload {value}.")
        else:
            self.log.warning(f"Could not publish telegram to group address {group_address} with payload {value}. XKNX is not started.")
