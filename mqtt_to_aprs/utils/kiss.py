from ..config import KissConfig
from asyncstdlib.functools import lru_cache as alru_cache
from asyncio import Queue
from asyncio import CancelledError
from uuid import uuid4
import logging

class KissSender:
    def __init__(self, config: KissConfig, sender_id: str = None)->None:
        self._config = config
        self.sender_id = uuid4() if sender_id is None else sender_id

    async def connect(self):
        logging.debug("Connect called for KissSender %s", self.sender_id)
        logging.debug("Connect done for KissSender %s", self.sender_id)

    async def disconnect(self):
        logging.debug("Disconnect called for KissSender %s", self.sender_id)
        logging.debug("Disconnect done for KissSender %s", self.sender_id)
        pass

    async def run(self, queue: Queue) -> None:
        logging.debug("Run starting KissSender %s", self.sender_id)
        try:
            while True:
                item = await queue.get()
                if item is None:
                    # None can be used as a signal to stop monitoring
                    logging.debug("Run KissSender %s received None, stopping", self.sender_id)
                    break
                print(f"KissSender {self.sender_id} Received item: {item}")
        except CancelledError:
            # Handle cancellation if needed
            logging.debug("Run KissSender %s cancelled", self.sender_id)
        finally:
            logging.debug("Run KissSender %s stopped", self.sender_id)



@alru_cache
async def get_kiss_sender(config: KissConfig, sender_id: str | None = None) -> KissSender:
    """Returns a connected KISS client"""
    this_sender = KissSender(config=config, sender_id=sender_id)
    await this_sender.connect()
    return this_sender
