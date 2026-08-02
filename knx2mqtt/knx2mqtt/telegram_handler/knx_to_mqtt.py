import logging

from ..adapter.knx import KnxAdapter
from ..adapter.mqtt import MqttAdapter

from xknx.telegram import TelegramDirection


class KnxToMqtt:

    def __init__(self, knx_adapter: KnxAdapter, mqtt_adapter: MqttAdapter):
        self._knx = knx_adapter
        self._mqtt = mqtt_adapter

        self.log = logging.getLogger(__name__)

        # Register callback functions
        self._knx.set_telegram_cb(self.on_telegram)

    def on_telegram(self, telegram):
        try:
            self.log.info("KNX telegram received: {}".format(telegram))

            if telegram.direction != TelegramDirection.INCOMING:
                return

            group_address = str(telegram.destination_address)
            value = self._knx.extract_value_from_telegram(group_address, telegram)

            # Publish on MQTT topic
            self._mqtt.publish(group_address, value)

            return True

        except Exception as e:
            self.log.error(e)
