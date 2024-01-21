from datetime import datetime, timezone

def hg_to_mbar(hg_val):
    """
    Convert inches of mercury (inHg to tenths of millibars/tenths of hPascals (mbar/hPa)
    :param hg_val: The value in inHg
    :return:
    """
    mbar = (hg_val / 0.029530) * 10

    return mbar

def str_or_dots(number, length):
    # If parameter is None, fill with dots, otherwise pad with zero
    if not number:
        retn_value = "." * length

    else:
        format_type = {"int": "d", "float": ".0f"}[type(number).__name__]

        retn_value = "".join(("%0", str(length), format_type)) % number

    return retn_value

def aprs_wx(wind_dir: float | None = None, wind_speed: float | None = None, wind_gust: float | None = None, temperature: float | None = None, rain_last_hr: float | None = None,
            rain_last_24_hrs: float | None = None, rain_since_midnight: float | None = None, humidity: float | None = None, pressure: float | None = None ):
    # Assemble the weather data of the APRS packet
    return "{}/{}g{}t{}r{}p{}P{}h{}b{}".format(
        str_or_dots(wind_dir, 3),
        str_or_dots(wind_speed, 3),
        str_or_dots(wind_gust, 3),
        str_or_dots(temperature, 3),
        str_or_dots(rain_last_hr, 3),
        str_or_dots(rain_last_24_hrs, 3),
        str_or_dots(rain_since_midnight, 3),
        str_or_dots(humidity, 2),
        str_or_dots(pressure, 5),
    )

def build_position_weather_packet(address: str, position: str, wx_data: str, send_id: str = "") -> str:
    """Creates a weather packet string"""
    utc_datetime = datetime.now(timezone.utc)
    packet_data = f"{address}@{utc_datetime.strftime('%d%H%M')}z{position}{wx_data}{send_id}"
    return packet_data
