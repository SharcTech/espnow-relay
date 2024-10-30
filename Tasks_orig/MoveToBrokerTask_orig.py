import uuid
import json
import logging
import asyncio
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue
import aiomqtt
from aiomqtt import MqttError


class MoveToBrokerTask:
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
                    await client.publish(f"espnow/{message['from_mac']}", message['message'].decode('utf-8'))

        except MqttError as e:
            self._logger.error("[broker] failed")

        self._logger.info("[broker] disconnected")
