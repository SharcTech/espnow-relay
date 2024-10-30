import uuid
import json
import logging
import asyncio
from asyncio import Event, Queue
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue
from brokers.Subscribing import Subscribing as SubscribingBroker


class MoveFromBrokerCustomTask:
    def __init__(self, to_esp_queue, peer_list, drop_invalid_peer, broker_ip, broker_port, broker_username, broker_password):
        self._to_esp_queue: MultisubscriberQueue = to_esp_queue
        self._peer_list = peer_list
        self._drop_invalid_peer = drop_invalid_peer
        self._broker_ip = broker_ip
        self._broker_port = broker_port
        self._broker_username = broker_username
        self._broker_password = broker_password
        self._broker_instance = None
        self._broker_queue = Queue()
        self._cancellation_event = Event()
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")

    async def run(self):
        self._logger.info("[run]")

        setup_task = asyncio.create_task(self._setup_task())
        await asyncio.gather(setup_task)

        self._broker_instance = SubscribingBroker(
            ip=self._broker_ip,
            port=self._broker_port,
            user=self._broker_username,
            password=self._broker_password,
            client_id=f"{self._unique_id}-source",
            topics=[
                {"topic": "sharc/+/cmd/#", "qos": 0}
            ],
            reconnect_s=5,
            message_queue=self._broker_queue,
            cancellation_event=self._cancellation_event,
            override_log_level=logging.INFO)

        broker_task = asyncio.create_task(self._broker_instance.run())
        esp_task = asyncio.create_task(self._esp_task())
        await asyncio.gather(broker_task, esp_task)

    async def _setup_task(self):
        self._logger.info("[setup]")

    async def _esp_task(self):
        self._logger.info("[esp] connecting")

        while True:
            broker_message = await self._broker_queue.get()

            topic = broker_message["topic"]
            payload = broker_message["payload"]
            self._logger.info("received on:%s, data:%s", topic, payload)

            try:
                serial = topic.split("/", 2)[1]

                if self._drop_invalid_peer == 1:
                    serial_mac = ':'.join(serial[i:i+2] for i in range(0, len(serial), 2)).upper()
                    if serial_mac not in self._peer_list:
                        self._logger.info("[esp] drop incoming message, %s not an active peer" % serial_mac)
                        continue

                command = topic.split("/", 3)[-1]
                payload = json.loads(payload)
                identifier = payload["id"]
                command_payload = payload["v"]
                mac_addr = ':'.join(serial[i:i+2] for i in range(0, len(serial), 2))

                if command == 'action':
                    if "device.reset" in command_payload:
                        message = {
                            'from_mac': "FF:FF:FF:FF:FF:FF",
                            'to_mac': mac_addr,
                            'message': b'|0|CMD|ACT|RST'
                        }
                        await self._to_esp_queue.put(message)
                    elif "io.publish" in command_payload:
                        message = {
                            'from_mac': "FF:FF:FF:FF:FF:FF",
                            'to_mac': mac_addr,
                            'message': b'|0|CMD|ACT|IO'
                        }
                        await self._to_esp_queue.put(message)
                    elif "di.counter.reset" in command_payload:
                        message = {
                            'from_mac': "FF:FF:FF:FF:FF:FF",
                            'to_mac': mac_addr,
                            'message': b'|0|CMD|ACT|COUNTER|0'
                        }
                        await self._to_esp_queue.put(message)
                    else:
                        pass
                elif command == 'cfg':
                    for key in command_payload:
                        message = {
                            'from_mac': "FF:FF:FF:FF:FF:FF",
                            'to_mac': mac_addr,
                            'message': b'|0|CMD|CFG|%s|%s' % (key, command_payload[key])
                        }
                        await self._to_esp_queue.put(message)

            except Exception as e:
                self._logger.exception("[esp] command parser failed, payload: %s" % payload)

        self._logger.info("[esp] disconnected")
