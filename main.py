import os
import sys
import logging
import asyncio
from asyncio import Queue

logging.basicConfig(level=int(os.getenv("LOG_LEVEL", 20)))
logger = logging.getLogger("main")
logger.info("espnow-relay starting")

async def main():
    tasks = []

    from_esp_queue = Queue()
    to_esp_queue = Queue()

    from Tasks.ESPNOWTask import ESPNOWTask
    tasks.append(asyncio.create_task(ESPNOWTask(
        from_esp_queue=from_esp_queue,
        to_esp_queue=to_esp_queue,
        interface=str(os.getenv("INTERFACE", "wlxc01c3038d5a8"))
    ).run()))

    from Tasks.ToESPSimulator import ToESPSimulator
    tasks.append(asyncio.create_task(ToESPSimulator(
        to_esp_queue=to_esp_queue
    ).run()))

    from Tasks.MoveToBrokerTask import MoveToBrokerTask
    tasks.append(asyncio.create_task(MoveToBrokerTask(
        from_esp_queue=from_esp_queue,
        broker_ip=str(os.getenv("BROKER_IP", "sharc.tech")),
        broker_port=int(os.getenv("BROKER_PORT", 1883)),
        broker_username=str(os.getenv("BROKER_USERNAME", None)),
        broker_password=str(os.getenv("BROKER_PASSWORD", None))
    ).run()))

    await asyncio.gather(*tasks)




if __name__ in ["__main__"]:
    # https://github.com/sbtinstruments/aiomqtt#note-for-windows-users
    # Change to the "Selector" event loop if platform is Windows
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())