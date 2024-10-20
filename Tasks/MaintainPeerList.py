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
        await self.send_ping("FF:FF:FF:FF:FF:FF")

    async def send_ping(self, peer):
        message = {
            'from_mac': "FF:FF:FF:FF:FF:FF",
            'to_mac': peer,
            'message': b'|0|CMD|ACT|PING'
        }
        await self._to_esp_queue.put(message)

    async def send_birth_certificate(self, peer):
        message = {
            'from_mac': peer,
            'to_mac': "FF:FF:FF:FF:FF:FF",
            'message': b'|0|EVT|AVAIL|1'
        }
        await self._from_esp_queue.put(message)
        self._logger.info(f"Fake birth certificate: {peer}")

    async def send_death_certificate(self, peer):
        message = {
            'from_mac': peer,
            'to_mac': "FF:FF:FF:FF:FF:FF",
            'message': b'|0|EVT|AVAIL|0'
        }
        await self._from_esp_queue.put(message)
        self._logger.info(f"Fake death certificate: {peer}")

    def upsert_peer(self, peer, is_alive):
        if peer in self._peers:
            self._peers[peer]['alive'] = is_alive
            self._peers[peer]['pong'] = time.monotonic()
            self._logger.debug(f"Peer updated: {peer}, Alive: {is_alive}")
        else:
            self._peers[peer] = {
                'alive': is_alive,
                'ping': time.monotonic(),
                'pong': time.monotonic()
            }
            self._logger.info(f"Peer added: {peer}, Alive: {is_alive}")

    async def _receive_task(self):
        self._logger.info("[receive_task]")

        async for message in self._from_esp_queue.subscribe():
            try:
                message_segments = [item for item in message['message'].decode('utf-8').split("|") if item]

                if message_segments[2].upper() == 'AVAIL':
                    self.upsert_peer(message['from_mac'], True if message_segments[3] == "1" else False)

                elif message_segments[2].upper() == 'ACK':
                    if message['from_mac'] not in self._peers:
                        await self.send_birth_certificate(message['from_mac'])

                    self.upsert_peer(message['from_mac'], True)

                else:
                    if message['from_mac'] not in self._peers:
                        await self.send_birth_certificate(message['from_mac'])

                    self.upsert_peer(message['from_mac'], True)
            except:
                self._logger.warning("[receive_task] failed parser, message:%s", message['message'])

    async def _expire_task(self):
        self._logger.info("[expire_task]")

        while True:
            delete_list = []
            await asyncio.sleep(10)
            for peer in self._peers:
                # print(f"{peer}, ping: {self._peers[peer]['ping']}, pong:{self._peers[peer]['pong']}")
                if self._peers[peer]['alive'] is True and self._peers[peer]['pong'] < self._peers[peer]['ping'] and time.monotonic() - self._peers[peer]['ping'] > 9:
                    delete_list.append(peer)
                    self._logger.warning(f"Peer expired: {peer}")
                    await self.send_death_certificate(peer)
                else:
                    await self.send_ping(peer)
                    self._peers[peer]['ping'] = time.monotonic()

            for peer in delete_list:
                del self._peers[peer]