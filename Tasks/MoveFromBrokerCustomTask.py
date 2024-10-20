import uuid
import json
import logging
import asyncio
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue
import aiomqtt
from aiomqtt import MqttError


class MoveFromBrokerCustomTask:
    def __init__(self, to_esp_queue, broker_ip, broker_port, broker_username, broker_password):
        self._broker_ip = broker_ip
        self._broker_port = broker_port
        self._broker_username = broker_username
        self._broker_password = broker_password
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._queue: MultisubscriberQueue = to_esp_queue

    async def run(self):
        self._logger.info("[run]")

        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        broker_task = asyncio.create_task(self._broker_task())
        await asyncio.gather(broker_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

    async def _broker_task(self):
        self._logger.info("[broker] connecting")

        try:
            topics = [
                {
                    "topic": "sharc/+/cmd/#",
                    "qos": 0
                }
            ]

            client = aiomqtt.Client(
                    hostname=self._broker_ip,
                    port=self._broker_port,
                    username=self._broker_username,
                    password=self._broker_password,
                    identifier=self._unique_id,
                    clean_session=True,
                    keepalive=60)

            async with client:
                self.logger.info("connected")

                for topic in topics:
                    self.logger.debug("subscribing: %s", topic["topic"])
                    await client.subscribe(
                        topic=topic["topic"],
                        qos=topic["qos"] if "qos" in topic else 0)

                async for message in client.messages:
                    topic = message.topic.value
                    payload = message.payload.decode('utf-8')
                    self.logger.debug("received on:%s, data:%s", topic, payload)

                    try:
                        serial = message["topic"].split("/", 2)[1]
                        command = message["topic"].split("/", 3)[-1]
                        payload = json.loads(message["payload"])
                        identifier = payload["id"]
                        command_payload = payload["v"]
                        mac_addr = ':'.join(serial[i:i+2] for i in range(0, len(serial), 2))

                        if command == 'action':
                            if "device.reset" in command_payload:
                                message = {
                                    'from_mac': "FF:FF:FF:FF:FF:FF",
                                    'to_mac': mac_addr,
                                    'message': b'|0|CMD|ACT|RST'
                                }
                                await self._queue.put(message)
                            elif "io.publish" in command_payload:
                                message = {
                                    'from_mac': "FF:FF:FF:FF:FF:FF",
                                    'to_mac': mac_addr,
                                    'message': b'|0|CMD|ACT|IO'
                                }
                                await self._queue.put(message)
                            else:
                                pass
                        elif command == 'cfg':
                            for key in command_payload:
                                message = {
                                    'from_mac': "FF:FF:FF:FF:FF:FF",
                                    'to_mac': mac_addr,
                                    'message': b'|0|CMD|CFG|%s|%s' % (key, command_payload[key])
                                }
                                await self._queue.put(message)

                    except Exception as e:
                        self._logger.exception("[broker] command parser failed")

        except MqttError as e:
            self._logger.error("[broker] failed")

        self._logger.info("[broker] disconnected")
