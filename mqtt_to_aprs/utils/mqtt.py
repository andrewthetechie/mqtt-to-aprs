from ..config import MQTTTopicConfig
from asyncstdlib.functools import lru_cache as alru_cache
from asyncio import Queue
from asyncio import CancelledError
from uuid import uuid4
import logging
from aiomqtt import Client
from aiomqtt.message import Message
from ..config import MQTTTopicTypes
from ..config import APRSOutputTypes
from ..config import MQTTTopicFieldsConfig
import json

class MQTTListener:
    def __init__(self, config: MQTTTopicConfig, mqtt_client: Client, queue: Queue, listener_id: str = None)->None:
        self._config: MQTTTopicConfig = config
        self.client: Client = mqtt_client
        self.listener_id: str = str(uuid4()) if listener_id is None else listener_id
        self.queue: Queue = queue

    async def connect(self):
        logging.debug("Connect called for MQTTListener %s", self.listener_id)
        logging.debug("Connect done for MQTTListener %s", self.listener_id)

    async def disconnect(self):
        logging.debug("Disconnect called for MQTTListener %s", self.listener_id)
        logging.debug("Disconnect done for MQTTListener %s", self.listener_id)
        pass

    async def listen(self) -> None:
        logging.debug("Listen starting MQTTListener %s", self.listener_id)
        try:
            while True:
                async with self.client as client:
                    await client.subscribe(self._config.topic)
                    async for message in client.messages:
                        packet_text = await translate_to_packet(message, self._config.input_type, self._config.output_type, self._config.fields)
                        await self.queue.put(f"Message from {self.listener_id}: {packet_text}")
        except CancelledError:
            # Handle cancellation if needed
            logging.debug("Run MQTTListener %s cancelled", self.listener_id)
        finally:
            logging.debug("Run MQTTListener %s stopped", self.listener_id)

async def translate_to_packet(message: Message, message_type: MQTTTopicTypes, packet_type: APRSOutputTypes, fields: MQTTTopicFieldsConfig) -> str:
    match message_type:
        case MQTTTopicTypes.json:
            message_data = await message_json(message)
        case _:
            raise NotImplementedError("Only JSON message processing is implemented at this time.")

    match packet_type:
        case APRSOutputTypes.weather:
            packet_text = await weather_data_from_message(message_data, fields)

        case _:
            raise NotImplementedError("Only Weather packet is implemented at this time")
    return packet_text

async def message_json(message: Message) -> dict[str, any]:
    """Convert a mqtt object to a python dict by reading JSON"""
    if isinstance(message.payload, bytes):
        payload = message.payload.decode('utf-8')
    elif isinstance(message.payload, str):
        payload = message.payload
    else:
        raise ValueError("Invalid Payload for a JSON message type. Payload must be str or bytes")
    try:
        data = json.loads(payload)
    except Exception as exc:
        raise ValueError(f"Error while parsing payload as json {exc}")
    return data

async def weather_data_from_message(data: dict[str, any], fields: MQTTTopicFieldsConfig) -> dict[str, any]:
    """Uses the fields config to convert the mqtt message's data into aprs weather data"""
    # TODO: read the aprs spec and make a weather packet from fields.
    # TODO: Define what fields can be in a weather packet
    print(data)

    return "I'm a fake weather packet"

@alru_cache
async def get_mqtt_listener(config: MQTTTopicConfig, mqtt_client: Client, queue: Queue, listener_id: str | None = None) -> MQTTListener:
    """Returns a connected KISS client"""
    this_listener = MQTTListener(config=config, mqtt_client=mqtt_client, queue=queue, listener_id=listener_id)
    await this_listener.connect()
    return this_listener
