import uuid
import json
import logging
import asyncio
from asyncio import Event
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue
from brokers.Publishing import Publishing as PublishingBroker


class MoveToBrokerCustomTask:
    def __init__(self, from_esp_queue, broker_ip, broker_port, broker_username, broker_password):
        self._from_esp_queue: MultisubscriberQueue = from_esp_queue
        self._broker_ip = broker_ip
        self._broker_port = broker_port
        self._broker_username = broker_username
        self._broker_password = broker_password
        self._broker_instance = None
        self._cancellation_event = Event()
        self._unique_id = str(uuid.uuid4())
        self._logger = logging.getLogger(f"({self._unique_id}) {self.__module__}")


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
            async for message in self._from_esp_queue.subscribe():
                try:
                    from_mac = message['from_mac'].replace(":", "").lower()
                    message_segments = [item for item in message['message'].decode('utf-8').split("|") if item]
                    message_topic = None
                    message_payload = None
                    message_retain = False
                    message_sequence = message_segments[0]
                    message_type = message_segments[1].upper()
                    message_subtype = message_segments[2].upper()
                    if message_type == 'EVT' and message_subtype == 'AVAIL':
                        message_retain = True
                        message_topic = f"sharc/{from_mac}/evt/avail"
                        message_payload = {
                            "seq": int(message_sequence),
                            "v": True if message_segments[3] == "1" else False,
                            "p2p": True
                        }
                    elif message_type == 'EVT' and message_subtype == 'IO':
                        sensor_type = message_segments[3].upper()
                        sensor_id = 's0' if sensor_type == 'PNP' else \
                                            's1' if sensor_type == 'NPN' else \
                                            's2' if sensor_type == '0-10V' else \
                                            's3' if sensor_type == '4-20MA' else \
                                            sensor_type.lower()
                        message_topic = f"sharc/{from_mac}/evt/io/{sensor_id}"
                        message_payload = {
                            "seq": int(message_segments[0]),
                            "v": {
                                "v": float(message_segments[4]),
                                "u": "unknown",
                                "d": int(message_segments[5])
                            }
                        }
                    elif message_type == 'EVT' and message_subtype == 'ACK':
                        message_topic = f"sharc/{from_mac}/evt/ack"
                        message_payload = {
                            "seq": int(message_segments[0]),
                            "v": {
                                "id": message_segments[3],
                                "rc": 0
                            }
                        }
                    else:
                        message_topic = f"sharc/{from_mac}/unk"
                        message_payload = {
                            "seq": int(message_segments[0]),
                            "v": message_segments
                        }

                    await self._broker_instance.publish(message_topic, json.dumps(message_payload), retain=message_retain)
                    self._logger.info("[broker] sent topic:%s, payload:%s",message_topic, message_payload)
                except:
                    self._logger.exception("[broker] failed parser, message: %s" % message['message'])

        except Exception as e:
            self._logger.error("[mq] failed")

        self._logger.info("[mq] donw")
