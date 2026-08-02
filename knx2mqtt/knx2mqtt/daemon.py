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
        KnxToMqtt(self._adapt_knx, self._adapt_mqtt)
        MqttToKnx(self._adapt_knx, self._adapt_mqtt)

    def run(self):
        self._adapt_mqtt.run()
        asyncio.run(
            self._adapt_knx.run()
        )
