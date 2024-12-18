import os
import sys
import logging
import asyncio
from libs.asyncio_multisubscriber_queue import MultisubscriberQueue

logging.basicConfig(level=int(os.getenv("LOG_LEVEL", 20)))
logger = logging.getLogger("main")
logger.info("espnow-relay starting")

async def main():
    tasks = []

    from_esp_queue = MultisubscriberQueue()
    to_esp_queue = MultisubscriberQueue()
    peer_list = {}

    from Tasks.ESPNOWTask import ESPNOWTask
    tasks.append(asyncio.create_task(ESPNOWTask(
        from_esp_queue=from_esp_queue,
        to_esp_queue=to_esp_queue,
        interface=str(os.getenv("INTERFACE", "wlxc01c3038d5a8"))
    ).run()))

    from Tasks.MoveToBrokerTask import MoveToBrokerTask
    tasks.append(asyncio.create_task(MoveToBrokerTask(
        from_esp_queue=from_esp_queue,
        broker_ip=str(os.getenv("BROKER_IP", "sharc.tech")),
        broker_port=int(os.getenv("BROKER_PORT", 1883)),
        broker_username=str(os.getenv("BROKER_USERNAME", None)),
        broker_password=str(os.getenv("BROKER_PASSWORD", None))
    ).run()))

    if int(os.getenv("ESP_TO_BROKER_CUSTOM", 0)) == 1:
        from Tasks.MoveToBrokerCustomTask import MoveToBrokerCustomTask
        tasks.append(asyncio.create_task(MoveToBrokerCustomTask(
            from_esp_queue=from_esp_queue,
            broker_ip=str(os.getenv("BROKER_IP", "sharc.tech")),
            broker_port=int(os.getenv("BROKER_PORT", 1883)),
            broker_username=str(os.getenv("BROKER_USERNAME", None)),
            broker_password=str(os.getenv("BROKER_PASSWORD", None))
        ).run()))

        from Tasks.MaintainPeerList import MaintainPeerList
        tasks.append(asyncio.create_task(MaintainPeerList(
            from_esp_queue=from_esp_queue,
            to_esp_queue=to_esp_queue,
            peer_list=peer_list
        ).run()))

    if int(os.getenv("BROKER_TO_ESP_CUSTOM", 0)) == 1:
        from Tasks.MoveFromBrokerCustomTask import MoveFromBrokerCustomTask
        tasks.append(asyncio.create_task(MoveFromBrokerCustomTask(
            to_esp_queue=to_esp_queue,
            peer_list=peer_list,
            drop_invalid_peer=int(os.getenv("DROP_INCOMING_INVALID_PEER", 1)),
            broker_ip=str(os.getenv("BROKER_IP", "sharc.tech")),
            broker_port=int(os.getenv("BROKER_PORT", 1883)),
            broker_username=str(os.getenv("BROKER_USERNAME", None)),
            broker_password=str(os.getenv("BROKER_PASSWORD", None))
        ).run()))

    #from Tasks.ToESPSimulator import ToESPSimulator
    #tasks.append(asyncio.create_task(ToESPSimulator(
    #    to_esp_queue=to_esp_queue
    #).run()))

    await asyncio.gather(*tasks)

    await from_esp_queue.close()
    await to_esp_queue.close()


if __name__ in ["__main__"]:
    # https://github.com/sbtinstruments/aiomqtt#note-for-windows-users
    # Change to the "Selector" event loop if platform is Windows
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())