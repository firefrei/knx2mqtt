import logging
import asyncio
import contextlib
import paho.mqtt.client as mqtt

from paho.mqtt.enums import CallbackAPIVersion


class PahoMqttAsyncioHelper:
    """Drive a Paho MQTT client from an existing asyncio loop."""

    def __init__(self, client: mqtt.Client, loop: asyncio.AbstractEventLoop):
        self._client = client
        self._loop = loop
        self._socket = None
        self._misc_task = None

        self._client.on_socket_open = self._on_socket_open
        self._client.on_socket_close = self._on_socket_close
        self._client.on_socket_register_write = (
            self._on_socket_register_write
        )
        self._client.on_socket_unregister_write = (
            self._on_socket_unregister_write
        )

    def _on_socket_open(self, client, userdata, sock):
        # connect() wird in asyncio.to_thread() ausgeführt.
        self._loop.call_soon_threadsafe(
            self._register_socket,
            sock,
        )

    def _register_socket(self, sock):
        self._socket = sock
        self._loop.add_reader(sock, self._handle_read)

        if self._misc_task is None or self._misc_task.done():
            self._misc_task = self._loop.create_task(
                self._misc_loop()
            )

    def _on_socket_close(self, client, userdata, sock):
        self._loop.call_soon_threadsafe(
            self._unregister_socket,
            sock,
        )

    def _unregister_socket(self, sock):
        self._loop.remove_reader(sock)
        self._loop.remove_writer(sock)

        if self._socket is sock:
            self._socket = None

    def _on_socket_register_write(self, client, userdata, sock):
        self._loop.call_soon_threadsafe(
            self._loop.add_writer,
            sock,
            self._handle_write,
        )

    def _on_socket_unregister_write(self, client, userdata, sock):
        self._loop.call_soon_threadsafe(
            self._loop.remove_writer,
            sock,
        )

    def _handle_read(self):
        self._client.loop_read()

    def _handle_write(self):
        self._client.loop_write()

    async def _misc_loop(self):
        try:
            while True:
                self._client.loop_misc()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise

    async def close(self):
        if self._socket is not None:
            self._unregister_socket(self._socket)

        if self._misc_task is not None:
            self._misc_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await self._misc_task

            self._misc_task = None    


class MqttAdapter:

    def __init__(self, config: dict, loop: asyncio.AbstractEventLoop):
        self._config = config
        self._loop = loop

        self.log = logging.getLogger(__name__)

    def init(self):
        """Create MQTT-Client object with user configuration"""
        self._client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=self._config['client_id'])
        if self._config['user'] or self._config['password']:
            self._client.username_pw_set(self._config['user'], self._config['password'])

        self._asyncio_helper = PahoMqttAsyncioHelper(self._client, self._loop)

    async def run(self):
        self._client.connect(self._config["host"], self._config["port"], keepalive=self._config["keepalive"])

    async def disconnect(self):
        self._client.disconnect()
        await self._asyncio_helper.close()

    def set_message_cb(self, cb):
        self._client.on_message = cb

    def set_connect_cb(self, cb):
        self._client.on_connect = cb

    def get_plain_topic(self, topic):
        return topic.replace("{}/".format(self._config["topic"]), "")

    def subscribe(self, topic):
        topic = "{}/{}".format(self._config['topic'], topic)
        self.log.info("Subscribing to topic: {0}".format(topic))
        self._client.subscribe(topic)

    def publish(self, topic, payload):
        topic = "{}/{}".format(self._config['topic'], topic)
        self.log.info("Publish %s: %s, %s, %s", topic, payload, self._config["qos"], self._config["retain"])

        try:
            self._client.publish(topic, payload, self._config["qos"], self._config["retain"])
        except Exception as e:
            self.log.error(e)
