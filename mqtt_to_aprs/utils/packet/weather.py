from datetime import datetime, timezone
import logging


def make_weather_data(wind_dir: float | None = None, wind_speed: float | None = None, wind_gust: float | None = None, temperature: float | None = None,
                 rain_last_hr: float | None = None, rain_last_24_hrs: float | None = None, rain_since_midnight: float | None = None,
                 humidity: float | None = None, pressure: float | None = None) -> str:

    def wx_fmt(value: int | float, length: int = 3):
        """converts a value into the appropriate number of digits or dots
        """
        return '.' * length if value is None else "{:0{l}d}".format(int(value), l=length)

    packet_string = ""
    # wind and speed
    packet_string += wx_fmt(wind_dir) + "/"
    packet_string += wx_fmt(wind_speed)
    packet_string += "g" + wx_fmt(wind_gust)
    if temperature is not None and int(temperature) <= -100:
        logging.debug("Temperature value %d is less than or equal to -100, rounding to -99", temperature)
        temperature = -99
    packet_string += "t" + wx_fmt(temperature)
    packet_string += "r" + wx_fmt(rain_last_hr)
    packet_string += "p" + wx_fmt(rain_last_24_hrs)
    packet_string += "P" + wx_fmt(rain_since_midnight)

    if humidity is not None:
        if int(humidity) >= 100:
            logging.debug("Humidity value %d is greater than or equal to 100, rounding to 00", humidity)
            packet_string += "h00"
        else:
            packet_string += "h" + wx_fmt(humidity, length=2)
    packet_string += "b" + wx_fmt(pressure, 5)

    return packet_string


def make_position_weather_packet(position: str, weather_data: str, send_id: str = "", timestamp: str = "") -> str:
    """Creates a weather packet string"""
    if timestamp == "":
        timestamp = datetime.now(timezone.utc).strftime('%d%H%M')
    packet_data = f"@{timestamp}z{position}{weather_data}w{send_id}"
    return packet_data
