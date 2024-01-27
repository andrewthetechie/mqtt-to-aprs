def decdeg2dms(degrees_decimal: float) -> dict[str, any]:
    is_positive = degrees_decimal >= 0
    degrees_decimal = abs(degrees_decimal)
    minutes, seconds = divmod(degrees_decimal * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees if is_positive else -degrees

    degrees = str(int(degrees)).zfill(2).replace("-", "0")
    minutes = str(int(minutes)).zfill(2).replace("-", "0")
    seconds = str(int(round(seconds * 0.01, 2) * 100)).zfill(2)

    return {"degrees": degrees, "minutes": minutes, "seconds": seconds}

def decdeg2dmm_m(degrees_decimal: float) -> dict[str, any]:
    is_positive = degrees_decimal >= 0
    degrees_decimal = abs(degrees_decimal)
    minutes, seconds = divmod(degrees_decimal * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees if is_positive else -degrees

    degrees = str(int(degrees)).zfill(2).replace("-", "0")
    minutes = str(round(minutes + (seconds / 60), 2)).zfill(5)

    return {"degrees": degrees, "minutes": minutes}

def convert_latitude(degrees_decimal: float) -> str:
    det = decdeg2dmm_m(degrees_decimal)
    if degrees_decimal > 0:
        direction = "N"
    else:
        direction = "S"

    degrees = det.get("degrees")
    minutes = det.get("minutes")

    lat = f"{degrees}{str(minutes)}{direction}"

    return lat

def convert_longitude(degrees_decimal: float) -> str:
    det = decdeg2dmm_m(degrees_decimal)
    if degrees_decimal > 0:
        direction = "E"
    else:
        direction = "W"

    degrees = det.get("degrees")
    minutes = det.get("minutes")

    lon = f"{degrees}{str(minutes)}{direction}"

    return lon


def make_position(latitude: float, longitude: float) -> str:
    """Convert a decimal latitude and longitude into an aprs position string"""
    return f"{convert_latitude(latitude)}/{convert_longitude(longitude)}_"


def address(callsign: str, path: str) -> str:
    """Converts a callsign into an address string"""
    match path:
        case "is":
            dest = "TCPIP*"
        case "kiss":
            raise NotImplementedError("KISS is not implemented yet")
        case _:
            raise NotImplementedError("Unknown path")
    return f"{callsign}>APRS,{dest}:"
