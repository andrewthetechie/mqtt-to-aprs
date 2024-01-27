from ..config import MQTTConfig, ConfigObject
from asyncio import Queue
from asyncio import CancelledError
from uuid import uuid4
import logging
from aiomqtt import Client
from ..config import MQTTTopicTypes
from ..config import TranslatorType
from ..config import APRSPacketTypes
from ..config import APRSOutputTargets
from .message.json import message_json
from collections.abc import Awaitable
from .translator.jmespath import JMESPathTranslator

class MQTTListener:
    def __init__(self, config: ConfigObject, mqtt_client: Client, internet_queue: Queue, kiss_queue: Queue, listener_id: str = None)->None:
        self._config: MQTTConfig = config.mqtt
        self._service_config: ConfigObject = config
        self._topic_names: list[str] = [topic.topic for topic in self._config.topics]
        self.client: Client = mqtt_client
        self.listener_id: str = str(uuid4()) if listener_id is None else listener_id
        self._internet_queue: Queue = internet_queue
        self._kiss_queue = kiss_queue
        self.translators: dict[str, Awaitable] = {}
        self.loaders: dict[str, Awaitable] = {}
        self.output_types: dict[str, APRSPacketTypes] = {}
        self.output_queues: dict[str, Queue] = {}
        self._is_connected = False

    async def connect(self):
        logging.debug("Connect called for MQTTListener %s", self.listener_id)
        for topic in self._config.topics:
            match topic.translator.type:
                case TranslatorType.jmespath:
                    self.translators[topic.topic] = JMESPathTranslator(topic.translator, self._service_config).translate
                case _:
                    raise NotImplementedError(f"{topic.translator.type} not a valid translator")

            match topic.input_type:
                case MQTTTopicTypes.json:
                    self.loaders[topic.topic] = message_json
                case _:
                    raise NotImplementedError(f"{topic.input_type} not a valid input type")

            match topic.target:
                case APRSOutputTargets.internet:
                    self.output_queues[topic.topic] = self._internet_queue

                case APRSOutputTargets.kiss:
                    self.output_queues[topic.topic] = self._kiss_queue

                case _:
                    raise NotImplementedError(f"{topic.target} is not a valid output target")

            self.output_types[topic.topic] = topic.output_type
        self._is_connected = True
        logging.debug("Connect done for MQTTListener %s", self.listener_id)

    async def disconnect(self):
        logging.debug("Disconnect called for MQTTListener %s", self.listener_id)
        self._is_connected = False
        logging.debug("Disconnect done for MQTTListener %s", self.listener_id)
        pass

    async def listen(self) -> None:
        logging.debug("Listen starting MQTTListener %s", self.listener_id)
        if not self._is_connected:
            await self.connect()
        try:
            while True:
                async with self.client as client:
                    for topic in self._topic_names:
                        await client.subscribe(topic)
                    async for message in client.messages:
                        message_topic = str(message.topic)
                        loader = self.loaders.get(message_topic, None)
                        if loader is None:
                            logging.error("Message from topic %s does not have a loader. Message payload: %s", message_topic, message.payload)
                            continue
                        message_data = await loader(message)
                        translator = self.translators.get(message_topic, None)
                        if translator is None:
                            logging.error("Message from topic %s does not have a translator.  Message payload: %s", message_topic, message.payload)
                            continue
                        packet_data = await translator(message_data, self.output_types.get(message_topic))
                        output_queue = self.output_queues.get(message_topic, None)
                        if output_queue is None:
                            logging.error("Message from topic %s does not have an output queue.  Message payload: %s", message_topic, message.payload)
                            continue
                        await output_queue.put(packet_data)
        except CancelledError:
            # Handle cancellation if needed
            logging.debug("Run MQTTListener %s cancelled", self.listener_id)
        finally:
            logging.debug("Run MQTTListener %s stopped", self.listener_id)


async def get_mqtt_listener(config: ConfigObject, mqtt_client: Client, queue: Queue, listener_id: str | None = None) -> MQTTListener:
    """Returns a connected KISS client"""
    this_listener = MQTTListener(config=config, mqtt_client=mqtt_client, queue=queue, listener_id=listener_id)
    await this_listener.connect()
    return this_listener
