import uuid
import json
import logging
import asyncio
from asyncio import Event, Queue
import aiomqtt
from aiomqtt import MqttError
from brokers.Publishing import Publishing as PublishingBroker
from ESPythoNOW import *


class TrafficSniffer:
    def __init__(self, broker_ip, broker_port, broker_username, broker_password, interface):
        self._broker_ip = broker_ip
        self._broker_port = broker_port
        self._broker_username = broker_username
        self._broker_password = broker_password
        self._interface = interface
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._queue = asyncio.Queue()
        self._espnow = None

    async def run(self):
        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        broker_task = asyncio.create_task(self._broker_task())
        await asyncio.gather(broker_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

        self._espnow = ESPythoNow(interface=self._interface, accept_all=True, callback=self._espnow_message_callback)
        self._espnow.start()

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

                while True:
                    message = await self._queue.get()
                    topic = f"espnow/{message['from_mac']}"
                    payload = message['message'],
                    await client.publish(topic, payload)
                    self._logger.debug("[broker] command sent topic:%s, payload:%s",
                                       topic, payload)

        except MqttError as e:
            self._logger.error("[broker] failed")

        self._logger.info("[broker] disconnected")

    async def _espnow_message_callback(self, from_mac, to_mac, msg):
        print("ESP-NOW message from %s to %s: %s" % (from_mac, to_mac, msg))
        message = {
            "from_mac": from_mac,
            "to_mac": to_mac,
            "message": msg
        }

        await self._queue.put(message)
