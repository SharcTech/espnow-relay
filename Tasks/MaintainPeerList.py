import uuid
import logging
import asyncio
import time
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue


class MaintainPeerList:
    def __init__(self, from_esp_queue, to_esp_queue):
        self._from_esp_queue: MultisubscriberQueue = from_esp_queue
        self._to_esp_queue: MultisubscriberQueue = to_esp_queue
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._peers = {}

    async def run(self):
        self._logger.info("[run]")
        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        receive_task = asyncio.create_task(self._receive_task())
        expire_task = asyncio.create_task(self._expire_task())
        await asyncio.gather(receive_task, expire_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

    async def _receive_task(self):
        self._logger.info("[receive_task]")

        async for message in self._from_esp_queue.subscribe():
            try:
                message_segments = [item for item in message['message'].decode('utf-8').split("|") if item]
                if message_segments[2].upper() == 'AVAIL':
                    if message['from_mac'] in self._peers:
                        self._peers[message['from_mac']]['alive'] = True if message_segments[3] == 1 else False
                        self._logger.info(f"Peer updated: {message['from_mac']}, Alive: {self._peers[message['from_mac']]['alive']}")
                    else:
                        self._peers[message['from_mac']] = {
                            'alive': True if message_segments[3] == 1 else False,
                            'ping': time.monotonic(),
                            'pong': time.monotonic()
                        }
                        self._logger.info(f"Peer added: {message['from_mac']}, Alive: {self._peers[message['from_mac']]['alive']}")
                elif message_segments[2].upper() == 'ACK':
                    if message['from_mac'] in self._peers:
                        self._peers[message['from_mac']]['alive'] = True
                        self._peers[message['from_mac']]['pong'] = time.monotonic()
                        self._logger.info(f"Peer updated: {message['from_mac']}, Alive: {self._peers[message['from_mac']]['alive']}")
                else:
                    if message['from_mac'] in self._peers:
                        self._peers[message['from_mac']]['alive'] = True
                        self._logger.debug(f"Peer updated: {message['from_mac']}, Alive: {self._peers[message['from_mac']]['alive']}")
                    else:
                        self._peers[message['from_mac']] = {
                            'alive': True
                        }
                        self._logger.info(f"Peer added: {message['from_mac']}, Alive: {self._peers[message['from_mac']]['alive']}")
            except:
                self._logger.warning("[receive_task] failed parser, message:%s", message['message'])

    async def _expire_task(self):
        self._logger.info("[expire_task]")

        while True:
            await asyncio.sleep(10)
            for peer in self._peers:
                if peer['pong'] < peer['ping'] and time.monotonic() - peer['ping'] > 9:
                    peer['alive'] = False
                    self._logger.warning(f"Peer expired: {peer}")