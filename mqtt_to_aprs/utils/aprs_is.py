from ..config import APRSConfig
from asyncstdlib.functools import lru_cache as alru_cache
from asyncio import BaseTransport
from aprs import APRSISProtocol
from asyncio import Queue
from asyncio import CancelledError
from uuid import uuid4
import logging


class APRSISSender:
    def __init__(self, config: APRSConfig, sender_id: str = None)->None:
        self._config = config
        self._transport: BaseTransport | None = None
        self.protocol : APRSISProtocol | None = None
        self.sender_id = uuid4() if sender_id is None else sender_id

    async def connect(self):
        logging.debug("Connect called for APRSISSender %s", self.sender_id)
        # self._tranport, self.protocol = await create_aprsis_connection(
        #     host=self._config.host,
        #     port=self._config.port,
        #     user=self._config.callsign_with_ssid,
        #     passcode=str(self._config.password),
        # )
        logging.debug("Connect done for APRSISSender %s", self.sender_id)

    async def disconnect(self):
        logging.debug("Disconnect called for APRSISSender %s", self.sender_id)
        self._transport, self.protocol = None, None
        logging.debug("Disconnect done for APRSISSender %s", self.sender_id)
        pass

    async def run(self, queue: Queue) -> None:
        logging.debug("Run starting APRSISSender %s", self.sender_id)
        try:
            while True:
                item = await queue.get()
                if item is None:
                    # None can be used as a signal to stop monitoring
                    logging.debug("Run APRSISSender %s received None, stopping", self.sender_id)
                    break
                print(f"APRSISSender {self.sender_id} Received item: {item}")
        except CancelledError:
            # Handle cancellation if needed
            logging.debug("Run APRSISSender %s cancelled", self.sender_id)
        finally:
            logging.debug("Run APRSISSender %s stopped", self.sender_id)


@alru_cache
async def get_aprsis_sender(config: APRSConfig, sender_id: str | None = None) -> APRSISSender:
    """Returns a connected aprsis client"""
    this_sender = APRSISSender(config=config, sender_id=sender_id)
    await this_sender.connect()
    return this_sender
