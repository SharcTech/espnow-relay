import uuid
import json
import logging
import asyncio
from asyncio import Queue
from ESPythoNOW import *


class ToESPSimulator:
    def __init__(self, to_esp_queue):
        self._to_esp_queue: Queue = to_esp_queue
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._counter = 100

    async def run(self):
        self._logger.info("[run]")
        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        send_task = asyncio.create_task(self._send_task())
        await asyncio.gather(send_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

    async def _send_task(self):
        self._logger.info("[receive_task]")

        while True:
            await asyncio.sleep(10)
            message = {
                'from_mac': "FF:FF:FF:FF:FF:FF",
                'to_mac': "FF:FF:FF:FF:FF:FF",
                # 'message': "counter".format(self._counter).encode('utf-8')
                'message': b'|1|CMD|PING'
            }
            self._counter = self._counter + 1
            await self._to_esp_queue.put(message)


