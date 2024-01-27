from ..config import ConfigObject
from .aprs_is import get_aprsis_sender, APRSISSender
from .kiss import get_kiss_sender, KissSender
from .mqtt import MQTTListener
from asyncio import Queue
from asyncio import create_task
from asyncio import gather
import logging
from aiomqtt import Client
from uuid import uuid4

class MQTT2APRS:
    def __init__(self, config: ConfigObject, service_id: str | None = None) -> None:
        self.config: ConfigObject = config
        self.is_setup: bool = False
        self.service_id = str(uuid4()) if service_id is None else service_id
        self._mqtt_listener: MQTTListener | None = None
        self._aprs_sender: APRSISSender | None = None
        self._aprs_sender_queue: Queue | None = None
        self._kiss_sender: KissSender | None = None
        self._kiss_sender_queue: Queue | None = None

    async def setup(self):
        """Gets the service ready to startup"""
        logging.debug("MQTT2APRS.setup called %s", self.service_id)
        if self.config.aprs.callsign is not None:
            logging.debug("Starting APRS Sender")
            self._aprs_sender = await get_aprsis_sender(config=self.config.aprs, sender_id=f"{self.service_id}-aprsis-1")
            self._aprs_sender_queue = Queue()

        if self.config.kiss.path is not None and self.config.kiss.path != "":
            logging.debug("Starting KISS Sender")
            self._kiss_sender = await get_kiss_sender(config=self.config.kiss, sender_id=f"{self.service_id}-kiss-1")
            self._kiss_sender_queue = Queue()

        self._mqtt_listener = MQTTListener(
            config=self.config,
            mqtt_client=Client(**self.config.mqtt.client_args, identifier=f"mqtt2aprs-{self.service_id}"),
            internet_queue=self._aprs_sender_queue,
            kiss_queue=self._kiss_sender_queue,
            listener_id=f"{self.service_id}-listener")

        self.is_setup = True

    async def run(self):
        # start the listeners and senders
        if not self.is_setup:
            await self.setup()

        mqtt_listener_tasks = [create_task(self._mqtt_listener.listen())]
        sender_tasks = []
        queues = []
        if self._aprs_sender is not None:
            sender_tasks.append(create_task(self._aprs_sender.run(self._aprs_sender_queue)))
            queues.append(self._aprs_sender_queue)
        if self._kiss_sender is not None:
            sender_tasks.append(create_task(self._kiss_sender.run(self._kiss_sender_queue)))
            queues.append(self._kiss_sender_queue)


        # with both listeners and senders running, wait for
        # the listeners to finish publishing
        await gather(*mqtt_listener_tasks)

        # wait for the remaining tasks to be processed
        for queue in ['_aprs_sender_queue', '_kiss_sender_queue']:
            logging.debug(f"Waiting for {queue} to be empty")
            await getattr(self, queue).join()

        # cancel the senders, which are now idle
        for task in sender_tasks:
            task.cancel()
