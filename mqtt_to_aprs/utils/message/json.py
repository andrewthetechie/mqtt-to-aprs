from aiomqtt.message import Message
import json


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
