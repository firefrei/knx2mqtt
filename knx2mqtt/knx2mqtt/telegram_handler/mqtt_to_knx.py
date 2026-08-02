import asyncio
import logging

from xknx.telegram import GroupAddress

from ..adapter.knx import KnxAdapter
from ..adapter.mqtt import MqttAdapter


class MqttToKnx:

    def __init__(self, knx_adapter: KnxAdapter, mqtt_adapter: MqttAdapter, mqtt_subscriptions: list = None):
        self._knx = knx_adapter
        self._mqtt = mqtt_adapter
        self._subscriptions = mqtt_subscriptions

        self.log = logging.getLogger(__name__)

        # Register callback functions
        self._mqtt.set_message_cb(self.on_message)
        self._mqtt.set_connect_cb(self.on_connect)

    def on_message(self, client, userdata, message):
        try:
            self.log.info("MQTT message received.")

            topic = message.topic
            value = str(message.payload.decode())

            # Get KNX group address
            address = self._mqtt.get_plain_topic(topic)
            group_address = GroupAddress(address)

            self.log.debug(f"Message {value} for topic {topic} --> KNX group address {group_address}.")

            # Construct KNX value
            dpt_value, dpt_type = self._knx.create_dpt_value(address, value)

            # Publish dpt value on KNX bus from the MQTT callback context.
            asyncio.run_coroutine_threadsafe(
                self._knx.publish(group_address, dpt_value, dpt_type),
                self._mqtt._loop,
            )

            return True

        except Exception as e:
            self.log.error(e)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        try:
            self.log.info("MQTT broker connection established.")

            for topic in self._subscriptions:
                self._mqtt.subscribe(topic)

            return True

        except Exception as e:
            self.log.error(e)
