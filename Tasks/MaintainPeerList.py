import uuid
import logging
import asyncio
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue


class MaintainPeerList:
    def __init__(self, from_esp_queue):
        self._from_esp_queue: MultisubscriberQueue = from_esp_queue
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._peers = {}

    async def run(self):
        self._logger.info("[run]")
        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        receive_task = asyncio.create_task(self._receive_task())
        await asyncio.gather(receive_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

    async def _receive_task(self):
        self._logger.info("[receive_task]")

        async for message in self._from_esp_queue.subscribe():
            try:
                message_segments = [item for item in message['message'].split("|") if item]
                if message_segments[2].upper() == 'AVAIL':
                    if message['from_mac'] in self._peers:
                        self._peers[message['from_mac']]['alive'] = True if message_segments[3] == 1 else False
                        self._logger.info(f"Peer added: {message['from_mac']}, Alive: {self._peers[message['from_mac']]['alive']}")
                    else:
                        self._peers[message['from_mac']] = {
                            'alive': True if message_segments[3] == 1 else False
                        }
                        self._logger.info(f"Peer updated: {message['from_mac']}, Alive: {self._peers[message['from_mac']]['alive']}")
            except:
                pass
