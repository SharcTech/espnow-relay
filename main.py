import os
import sys
import logging
import asyncio
from asyncio import Queue

logging.basicConfig(level=20)
logger = logging.getLogger("main")
logger.info("espnow-relay starting")

async def main():
    tasks = []

    from_esp_queue = Queue()
    to_esp_queue = Queue()

    from ESPNOWTask import ESPNOWTask
    tasks.append(asyncio.create_task(ESPNOWTask(
        from_esp_queue=from_esp_queue,
        to_esp_queue=to_esp_queue,
        interface="wlxc01c3038d5a8"
    ).run()))

    #from TrafficSniffer import TrafficSniffer
    #tasks.append(asyncio.create_task(TrafficSniffer(
    #    broker_ip="sharc.tech",
    #    broker_port=1883,
    #    broker_username=None,
    #    broker_password=None,
    #    interface="wlxc01c3038d5a8"
    #).run()))

    await asyncio.gather(*tasks)




if __name__ in ["__main__"]:
    # https://github.com/sbtinstruments/aiomqtt#note-for-windows-users
    # Change to the "Selector" event loop if platform is Windows
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())