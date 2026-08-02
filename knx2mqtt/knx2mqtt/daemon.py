import asyncio

from .config import ConfigManager
from .mqtt.adapter import MqttAdapter
from .knx.adapter import KnxAdapter
from .knx.event_handler import KnxEventHandler
from .mqtt.event_handler import MqttEventHandler


class Daemon:

    def __init__(self, config_mgr: ConfigManager):
        self.config_mgr = config_mgr
        self._init_mqtt()
        self._init_knx()
        self._init_handler()

    def _init_mqtt(self):
        self._mqtt_adapt = MqttAdapter(self.config_mgr.mqtt)
        self._mqtt_adapt.init()

    def _init_knx(self):
        self._knx_adapt = KnxAdapter(self.config_mgr.knx)
        self._knx_adapt.init()

    def _init_handler(self):
        knx_address_filters, mqtt_subscriptions = self.config_mgr.generate_address_filters_and_subscriptions()

        self._knx_handler = KnxEventHandler(self._knx_adapt, self._mqtt_adapt, knx_address_filters=knx_address_filters)
        self._mqtt_handler = MqttEventHandler(self._knx_adapt, self._mqtt_adapt, mqtt_subscriptions=mqtt_subscriptions)

    async def run(self):
        self._mqtt_handler.set_loop(asyncio.get_running_loop())

        self._mqtt_adapt.run()
        await self._knx_adapt.run()
