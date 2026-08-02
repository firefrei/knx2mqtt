import asyncio
import logging

from xknx.telegram import GroupAddress

from ..knx.adapter import KnxAdapter
from .adapter import MqttAdapter


class MqttEventHandler:

    def __init__(self, knx_adapter: KnxAdapter, mqtt_adapter: MqttAdapter, mqtt_subscriptions: list = None):
        self._knx = knx_adapter
        self._mqtt = mqtt_adapter
        self._subscriptions = mqtt_subscriptions
        self._loop = None

        self.log = logging.getLogger(__name__)

        # Register callback functions
        self._mqtt.set_message_cb(self.on_message)
        self._mqtt.set_connect_cb(self.on_connect)
        self._mqtt.set_disconnect_cb(self.on_disconnect)
        self._mqtt.set_connect_fail_cb(self.on_connect_fail)

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def on_message(self, client, userdata, message):
        topic = message.topic
        value = str(message.payload.decode())

        self.log.info("MQTT message received on topic: {}".format(topic))

        # Get KNX group address
        address = self._mqtt.get_plain_topic(topic)
        group_address = GroupAddress(address)

        self.log.debug(f"Message {value} for topic {topic} --> KNX group address {group_address}.")

        # Construct KNX value
        dpt_value, dpt_type = self._knx.create_dpt_value(address, value)

        if self._loop is None:
            self.log.error("No event loop configured for MQTT callback. The callback was invoked before the asyncio loop was registered.")
            return

        # Publish dpt value on KNX bus from the MQTT callback context.
        asyncio.run_coroutine_threadsafe(
            self._knx.publish(group_address, dpt_value, dpt_type),
            self._loop
        )

    def on_connect(self, client, userdata, flags, reason_code, properties):
        # Log connection state
        self.log.info(
            "MQTT broker connection established [reason_code=%s, session_present=%s]",
            reason_code, flags.session_present
        )

        if reason_code.is_failure:
            self.log.error("MQTT connection rejected: %s", reason_code)
            return

        # Execute subscriptions on connect
        for topic in self._subscriptions:
            self._mqtt.subscribe(topic)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.log.warning(
            "MQTT broker connection disconnected [reason_code=%s, flags=%s, properties=%s]",
            reason_code, disconnect_flags, properties
        )
    
    def on_connect_fail(self, client, userdata):
        self.log.error("TCP connection to MQTT broker failed")
