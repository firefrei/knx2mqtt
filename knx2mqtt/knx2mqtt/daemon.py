import asyncio

from .config import ConfigManager
from .adapter.mqtt import MqttAdapter
from .adapter.knx import KnxAdapter
from .telegram_handler.knx_to_mqtt import KnxToMqtt
from .telegram_handler.mqtt_to_knx import MqttToKnx


class Daemon:

    def __init__(self, config_mgr: ConfigManager):
        self.config_mgr = config_mgr
        self._init_mqtt()
        self._init_knx()
        self._init_handler()

    def _init_mqtt(self):
        self._adapt_mqtt = MqttAdapter(self.config_mgr.mqtt)
        self._adapt_mqtt.init()

    def _init_knx(self):
        self._adapt_knx = KnxAdapter(self.config_mgr.knx)
        self._adapt_knx.init()

    def _init_handler(self):
        knx_address_filters, mqtt_subscriptions = self.config_mgr.generate_address_filters_and_subscriptions()
        KnxToMqtt(self._adapt_knx, self._adapt_mqtt, knx_address_filters=knx_address_filters)
        self._handler_mqtt = MqttToKnx(self._adapt_knx, self._adapt_mqtt, mqtt_subscriptions=mqtt_subscriptions)

    async def run(self):
        self._handler_mqtt.set_loop(asyncio.get_running_loop())
        self._adapt_mqtt.run()
        await self._adapt_knx.run()
