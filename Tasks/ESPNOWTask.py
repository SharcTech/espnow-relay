import uuid
import logging
import asyncio
from asyncio import Queue
from ESPythoNOW import *


class ESPNOWTask:
    def __init__(self, interface, to_esp_queue, from_esp_queue):
        self._interface = interface
        self._to_esp_queue: Queue = to_esp_queue
        self._from_esp_queue: Queue = from_esp_queue
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._espnow = None

    async def run(self):
        self._logger.info("[run]")
        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        receive_task = asyncio.create_task(self._receive_task())
        await asyncio.gather(receive_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

        self._espnow = ESPythoNow(interface=self._interface, accept_all=True, callback=self._espnow_message_callback)
        self._espnow.start()

    async def _receive_task(self):
        self._logger.info("[receive_task]")

        while True:
            message = await self._to_esp_queue.get()
            print("ESP-NOW SEND to: %s, msg: %s" % (message["to_mac"], message["message"]))
            self._espnow.send(message["to_mac"], message["message"])

    def _espnow_message_callback(self, from_mac, to_mac, msg):
        print("ESP-NOW RECV from: %s, to: %s, msg: %s" % (from_mac, to_mac, msg))
        message = {
            "from_mac": from_mac,
            "to_mac": to_mac,
            "message": msg
        }

        self._from_esp_queue.put_nowait(message)
