import uuid
import json
import logging
import asyncio
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue
import aiomqtt
from aiomqtt import MqttError


class MoveToBrokerCustomTask:
    def __init__(self, from_esp_queue, broker_ip, broker_port, broker_username, broker_password):
        self._broker_ip = broker_ip
        self._broker_port = broker_port
        self._broker_username = broker_username
        self._broker_password = broker_password
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._queue: MultisubscriberQueue = from_esp_queue

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
            async with aiomqtt.Client(
                    hostname=self._broker_ip,
                    port=self._broker_port,
                    username=self._broker_username,
                    password=self._broker_password,
                    identifier=self._unique_id,
                    clean_session=True,
                    keepalive=60) as client:

                self._logger.info("[broker] connected")

                async for message in self._queue.subscribe():
                    try:
                        from_mac = message['from_mac'].replace(":", "").lower()
                        message_segments = [item for item in message['message'].decode('utf-8').split("|") if item]
                        message_topic = None
                        message_payload = None
                        message_retain = False
                        message_sequence = message_segments[0]
                        message_type = message_segments[1].upper()
                        message_subtype = message_segments[2].upper()
                        if message_type == 'EVT' and message_subtype == 'AVAIL':
                            message_retain = True
                            message_topic = f"sharc/{from_mac}/evt/avail"
                            message_payload = {
                                "seq": message_sequence,
                                "v": True if message_segments[3] == "1" else False,
                                "p2p": True
                            }
                        elif message_type == 'EVT' and message_subtype == 'IO':
                            sensor_type = message_segments[3].upper()
                            sensor_id = 's0' if sensor_type == 'PNP' else \
                                                's1' if sensor_type == 'NPN' else \
                                                's2' if sensor_type == '0-10V' else \
                                                's3' if sensor_type == '4-20MA' else \
                                                sensor_type.lower()
                            message_topic = f"sharc/{from_mac}/evt/io/{sensor_id}"
                            message_payload = {
                                "seq": message_segments[0],
                                "v": message_segments[4],
                                "d": message_segments[5]
                            }
                        elif message_type == 'EVT' and message_subtype == 'ACK':
                            message_topic = f"sharc/{from_mac}/evt/ack"
                            message_payload = {
                                "seq": message_segments[0],
                                "v": {
                                    "id": message_segments[3],
                                    "rc": 0
                                }
                            }
                        else:
                            message_topic = f"sharc/{from_mac}/unk"
                            message_payload = {
                                "seq": message_segments[0],
                                "v": message_segments
                            }

                        await client.publish(message_topic, json.dumps(message_payload), retain=message_retain)
                        self._logger.info("[broker] sent topic:%s, payload:%s",message_topic, message_payload)
                    except:
                        self._logger.warning("[broker] failed parser, message:%s", message['message'])

        except MqttError as e:
            self._logger.error("[broker] failed")

        self._logger.info("[broker] disconnected")
