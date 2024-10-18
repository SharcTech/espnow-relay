import uuid
import json
import logging
import asyncio
from asyncio import Event, Queue
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
        self._cancellation_event = Event()
        self._queue = Queue()
        self._broker = None
        self._espnow = None

    async def run(self):
        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        self._broker = PublishingBroker(
            ip=self._broker_ip,
            port=self._broker_port,
            user=self._broker_username,
            password=self._broker_password,
            client_id=self._unique_id,
            reconnect_s=5,
            cancellation_event=self._cancellation_event)

        feed_task = asyncio.create_task(self._feed_task())
        broker_task = asyncio.create_task(self._broker.run())
        await asyncio.gather(feed_task, broker_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

        #self._espnow = ESPythoNow(interface=self._interface, accept_all=True, callback=self._espnow_message_callback)
        #self._espnow.start()

    async def _feed_task(self):
        counter = 1
        while True:
            await asyncio.sleep(4)
            await self._broker.publish("feed/task", "feeding {}".format(counter))
            counter = counter + 1

    def _espnow_message_callback(self, from_mac, to_mac, msg):
        print("ESP-NOW message from %s to %s: %s" % (from_mac, to_mac, msg))
        self._broker.publish("espnow/{}".format(from_mac), msg.decode('utf-8'))