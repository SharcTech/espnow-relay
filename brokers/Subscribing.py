import logging
import asyncio
from asyncio import Event, Queue
import aiomqtt
from aiomqtt import MqttError


class Subscribing:
    def __init__(self,
                 ip: str,
                 port: int,
                 user: str | None,
                 password: str | None,
                 client_id: str,
                 topics: list,
                 reconnect_s: int,
                 message_queue: Queue,
                 cancellation_event: Event,
                 override_log_level: int = None):
        self._ip = ip
        self._port = port
        self._user = user
        self._password = password
        self._topics = topics
        self._reconnect_s = reconnect_s
        self._client_id = client_id
        self._message_queue = message_queue
        self._cancellation_event = cancellation_event
        self._task: asyncio.Task | None = None
        self.logger = logging.getLogger(f"({self._client_id}) {self.__module__}")
        if override_log_level is not None:
            self.logger.setLevel(override_log_level)

    async def run(self):
        self._task = asyncio.create_task(self._broker_task())

    async def _handle_broker_message(self, message):
        self.logger.debug("received on:%s, data:%s",
                          message.topic.value, message.payload.decode('utf-8'))
        if self._message_queue:
            await self._message_queue.put({
                "topic": message.topic.value,
                "payload": message.payload.decode('utf-8')
            })

    async def _iterate_broker_messages_task(self, client):
        async for message in client.messages:
            await asyncio.shield(self._handle_broker_message(message))

    async def _broker_task(self):
        while not self._cancellation_event.is_set():
            try:
                self.logger.info("connecting %s:%d",
                                 self._ip,
                                 self._port)

                client = aiomqtt.Client(
                    hostname=self._ip,
                    port=self._port,
                    username=self._user,
                    password=self._password,
                    identifier=self._client_id,
                    clean_session=True,
                    keepalive=60)

                async with client:
                    self.logger.info("connected")

                    for topic in self._topics:
                        self.logger.debug("subscribing: %s", topic["topic"])
                        await client.subscribe(
                            topic=topic["topic"],
                            qos=topic["qos"] if "qos" in topic else 0)

                    message_task = asyncio.create_task(self._iterate_broker_messages_task(client))
                    close_task = asyncio.create_task(self._cancellation_event.wait())
                    await asyncio.wait([message_task, close_task], return_when=asyncio.FIRST_COMPLETED)

                    if message_task.done():
                        message_task.result()
                        close_task.cancel()
                    else:
                        message_task.cancel()

            except MqttError as e:
                self.logger.error("failed")
                message_task.cancel()
                close_task.cancel()
                await asyncio.sleep(self._reconnect_s)

        self.logger.info("disconnected")