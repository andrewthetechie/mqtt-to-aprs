# translates a mqtt message to an aprs packet
from . import Translator
from aprs import InformationField, PositionReport
from ...config import APRSPacketTypes
from ...config import JMESPathWeatherFields
from functools import lru_cache
import jmespath
from jmespath.parser import ParsedResult
import logging
from ..packet.weather import make_position_weather_packet, make_weather_data
from ..packet import make_position


class JMESPathTranslator(Translator):
    async def translate(self, message_data: dict[str, any], packet_type: APRSPacketTypes) -> InformationField:
        match packet_type:
            case APRSPacketTypes.weather:
                message_data = jmespath_weather_fields(message_data, self._translator_config.fields)
                latitude = message_data.pop("latitude", None)
                longitude = message_data.pop("longitude", None)
                if latitude is None:
                    latitude = self._service_config.location.latitude
                if longitude is None:
                    longitude = self._service_config.location.longitude
                position = make_position(latitude=latitude, longitude=longitude)
                packet_data = make_position_weather_packet(position=position,
                                                           weather_data=make_weather_data(**message_data))
                field = PositionReport.from_bytes(packet_data.encode('utf-8'))

            case _:
                raise NotImplementedError("Invalid packet_type")
        return field


def jmespath_weather_fields(message_data: dict[str, any], fields: JMESPathWeatherFields) -> dict[str, any]:
    """Uses jmespath to translate fields in the mqtt message into values for eather data

    Args:
        message_data (dict[str, any]): _description_
        fields (JMESPathWeatherFields): _description_

    Returns:
        dict[str, any]: _description_
    """
    def hg_to_mbar(hg_val):
        """
        Convert inches of mercury (inHg to tenths of millibars/tenths of hPascals (mbar/hPa)
        :param hg_val: The value in inHg
        :return:
        """
        mbar = (hg_val / 0.029530) * 10

        return mbar

    def c_to_f(temperature_c: float) -> float:
        """Converts temperature celcius to fahrenheit"""
        return (1.8 * temperature_c) + 32


    weather_data = {
        "wind_dir": None,
        "wind_speed": None,
        "wind_gust": None,
        "temperature": None,
        "rain_last_hr": None,
        "rain_last_24_hrs": None,
        "rain_since_midnight": None,
        "humidity": None,
        "pressure": None,
        "latitude": None,
        "longitude": None
    }
    for key, value in fields.dict().items():
        if value is None:
            continue
        jmespath = get_compiled_jmespath(value)
        result = jmespath.search(message_data)
        if result is None:
            logging.warning("No matching %s at path %s", key, value)
            continue
        match key:
            case "temperature_f":
                weather_data["temperature"] = float(result)
            case "temperature_c":
                if weather_data["temperature"] is None:
                    weather_data["temperature"] = c_to_f(result)
            case "pressure_mbar":
                weather_data["pressure"] = float(result)
            case "pressure_hg":
                if weather_data["pressure"] is None:
                    weather_data["pressure"] = hg_to_mbar(float(result))

        # these variables are just direclty passed through, no translations applied
        direct_passthrough_variables = ['wind_dir', 'wind_speed', 'wind_gust', 'rain_last_hr', 'rain_last_24_hrs', 'rain_since_midnight', 'humidity', "latitude", "longitude"]
        if key in direct_passthrough_variables:
            weather_data[key] = result

    return weather_data


@lru_cache
def get_compiled_jmespath(search: str) -> ParsedResult:
    return jmespath.compile(search)
