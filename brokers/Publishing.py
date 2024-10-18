import logging
import asyncio
from asyncio import Event, Queue, Task
from aiomqtt import MqttError, Client


class Publishing:
    def __init__(self,
                 ip: str,
                 port: int,
                 user: str | None,
                 password: str | None,
                 client_id: str,
                 reconnect_s: int,
                 cancellation_event: Event,
                 override_log_level: int = None):
        self._ip = ip
        self._port = port
        self._user = user
        self._password = password
        self._reconnect_s = reconnect_s
        self._client_id = client_id
        self._cancellation_event = cancellation_event
        self._task: Task | None = None
        self._queue = Queue()
        self.logger = logging.getLogger(f"({self._client_id}) {self.__module__}")
        if override_log_level is not None:
            self.logger.setLevel(override_log_level)

    async def run(self):
        self._task = asyncio.create_task(self._broker_task())
        return self._task

    async def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        await self._queue.put({
            "topic": topic,
            "payload": payload,
            "qos": qos,
            "retain": retain
        })

    async def _iterate_broker_messages_task(self, client: Client):
        while not self._cancellation_event.is_set():
            message = await self._queue.get()
            self.logger.debug("publishing on:%s, data:%s",
                              message["topic"], message["payload"])
            await client.publish(message["topic"], message["payload"], message["qos"], message["retain"])

    async def _broker_task(self):
        while not self._cancellation_event.is_set():
            try:
                self.logger.info("connecting %s:%d",
                                 self._ip,
                                 self._port)

                client = Client(
                    hostname=self._ip,
                    port=self._port,
                    username=self._user,
                    password=self._password,
                    identifier=self._client_id,
                    clean_session=True,
                    keepalive=60)

                async with client:
                    self.logger.info("connected")

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