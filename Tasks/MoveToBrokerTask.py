import uuid
import json
import logging
import asyncio
from asyncio import Event
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue
from brokers.Publishing import Publishing as PublishingBroker


class MoveToBrokerTask:
    def __init__(self, from_esp_queue, broker_ip, broker_port, broker_username, broker_password):
        self._broker_ip = broker_ip
        self._broker_port = broker_port
        self._broker_username = broker_username
        self._broker_password = broker_password
        self._broker_instance = None
        self._cancellation_event = Event()
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")
        self._queue: MultisubscriberQueue = from_esp_queue

    async def run(self):
        self._logger.info("[run]")

        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        self._broker_instance = PublishingBroker(
            ip=self._broker_ip,
            port=self._broker_port,
            user=self._broker_username,
            password=self._broker_password,
            client_id=f"{self._unique_id}-target",
            reconnect_s=5,
            cancellation_event=self._cancellation_event,
            override_log_level=logging.INFO
        )

        broker_task = asyncio.create_task(self._broker_instance.run())
        message_queue_task = asyncio.create_task(self._message_queue())

        await asyncio.gather(broker_task, message_queue_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

    async def _message_queue(self):
        self._logger.info("[mq] starting")

        try:
            async for message in self._queue.subscribe():
                await self._broker_instance.publish(f"espnow/{message['from_mac']}", message['message'].decode('utf-8'))

        except Exception as e:
            self._logger.error("[mq] failed")

        self._logger.info("[mq] done")
