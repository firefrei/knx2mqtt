import logging
import paho.mqtt.client as mqtt

from paho.mqtt.enums import CallbackAPIVersion


class MqttAdapter:

    def __init__(self, config: dict):
        self._config = config

        self.log = logging.getLogger(__name__)

    def init(self):
        """Create MQTT-Client object with user configuration"""
        self._client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=self._config["client_id"])
        if self._config["user"] or self._config["password"]:
            self._client.username_pw_set(self._config["user"], self._config["password"])

    def run(self):
        self._client.connect_async(self._config["host"], self._config["port"], keepalive=self._config["keepalive"])
        self._client.loop_start()

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()

    def set_message_cb(self, cb):
        self._client.on_message = cb

    def set_connect_cb(self, cb):
        self._client.on_connect = cb
    
    def set_disconnect_cb(self, cb):
        self._client.on_disconnect = cb

    def set_connect_fail_cb(self, cb):
        self._client.on_connect_fail = cb

    def get_plain_topic(self, topic):
        return topic.replace("{}/".format(self._config["topic"]), "")

    def subscribe(self, topic):
        topic = "{}/{}".format(self._config["topic"], topic)
        result, message_id = self._client.subscribe(topic)
        self.log.info(
            "Subscribed to MQTT topic: %s [result=%s, mid=%s]",
            topic, result, message_id,
        )        

    def publish(self, topic, payload):
        topic = "{}/{}".format(self._config["topic"], topic)
        self.log.info("Publish %s: %s, %s, %s", topic, payload, self._config["qos"], self._config["retain"])

        try:
            self._client.publish(topic, payload, self._config["qos"], self._config["retain"])
        except Exception as e:
            self.log.error(e)
