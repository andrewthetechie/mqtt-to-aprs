from pydantic import BaseModel
from pydantic import Field
from pydantic import DirectoryPath

from enum import Enum
from pathlib import Path
from tomllib import load as toml_load
from tomllib import loads as toml_loads

import aiofiles
import os
import json
from functools import lru_cache
from functools import cached_property
from asyncstdlib.functools import lru_cache as alru_cache
from pydantic import ValidationError

DEFAULT_CONFIG_PATH = os.environ.get("MQTT2APRS_CONFIG", "/etc/mqtt2aprs/config.toml")

class LogLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"


class LoggingConfig(BaseModel):
    log_path: DirectoryPath | None = Field(None, description="Path to log to, leave as None to log to stdout")
    log_level: LogLevel = Field("INFO", description="Log level for the app")


class APRSConfig(BaseModel):
    callsign: str
    ssid: int | None = Field(None)
    password: int
    host: str = Field("rotate.aprs.net", description="APRS.is host to connect to")
    port: int = Field(10152, description="Port for the APRS.is host")

    @cached_property
    def callsign_with_ssid(self):
        """Returns the callsign with the SSID if the SSID is specified"""
        if self.ssid is not None:
            return f"{self.callsign}-{self.ssid}"
        return self.callsign

    def __hash__(self) -> int:
        return hash(f"{self.callsign_with_ssid}-{self.password}-{self.host}-{self.port}")


class KissConfig(BaseModel,):
    path: str | None = Field(None, description="Path to serial KISS path or tcp:// to connect over the network")

    def __hash__(self) -> int:
        return hash(self.path)


class LocationConfig(BaseModel):
    latitude: float | None = Field(None, description="Latitude")
    longitude: float | None = Field(None, description="Longitude")


class MQTTTopicTypes(str, Enum):
    json = "json"


class APRSOutputTypes(str, Enum):
    weather = "weather"


class APRSOutputTargets(str, Enum):
    internet = "is"
    kiss = "kiss"


class MQTTTopicFieldsConfig(BaseModel):
    # http://www.aprs.org/doc/APRS101.PDF
    # Chapter 12, weather packet format
    # We'll prebuild some converters for now for common stuff
    # Will eventually need a better transform layer here to do some basic math
    temperature_f: str | None = Field(None, description="JMSEPath to a Temperature in Fahrenheit")
    temperature_c: str | None = Field(None, description="JMSEPath to a Temperature in Celcius, will be converted to Fahrenheit")
    wind_dir: str | None = Field(None, description="JMSEPath to a Wind Direction in Degrees")
    wind_speed: str | None = Field(None, description="JMSEPath to Wind Speed value sustained one-minute wind speed (in mph).")
    wind_gust: str | None = Field(None, description="JMSEPath to a Gust Wind Speed (peak wind speed in mph in the last 5 minutes).")
    rain_last_hr: str | None = Field(None, description="JMSEPath to a rainfall (in hundredths of an inch) in the last hour")
    rain_last_24_hrs: str | None = Field(None, description="JMSEPath to a rainfall (in hundredths of an inch) in the last 24 hours")
    rain_since_midnight: str | None = Field(None, description="JMSEPath to a rainfall (in hundredths of an inch) since midnight")
    humidity: str | None = Field(None, description="JMSEPath to a humidity (in %. 00 = 100%).")
    pressure: str | None = Field(None, description="JMSEPath to a barometric pressure (in tenths of millibars/tenths of hPascal).")


class MQTTTopicConfig(BaseModel):
    topic: str
    input_type: MQTTTopicTypes = Field("json")
    output_type: APRSOutputTypes = Field("weather")
    target: APRSOutputTargets
    fields: MQTTTopicFieldsConfig

    @classmethod
    def load_from_env(cls) -> dict[str, any]:
        loaded = {}
        env_base = f"{cls.schema()['title'].strip('Config')}"
        for key in cls.schema().keys():
            if key == "fields":
                continue
            env_key = f"{env_base}_{key}".upper()
            value = os.environ.get(env_key, None)
            if value:
                loaded[key] = value
        fields = os.environ.get(f"{env_base}_fields", None)
        if fields is not None:
            loaded['fields'] = json.loads(fields)
        return loaded

    def __hash__(self) -> int:
        return hash(f"{self.topic}-{self.output_type}")

class MQTTConfig(BaseModel):
    host: str
    port: int
    username: str | None = Field(None, description="Username for the MQTT server, if auth is required")
    password: str | None = Field(None, description="Password for the MQTT server, if auth is required")
    topics: list[MQTTTopicConfig]

    @cached_property
    def client_args(self):
        this_args = {
            "hostname": self.host,
            "port": self.port,
        }
        if self.password is not None:
            this_args['username'] = self.username
            this_args['password'] = self.password
        return this_args


class ConfigObject(BaseModel):
    logging: LoggingConfig = Field(..., description="Configuration for logging")
    aprs: APRSConfig
    kiss: KissConfig
    location: LocationConfig
    mqtt: MQTTConfig

    @classmethod
    def from_toml(cls, toml_path: Path, include_env: bool = False) -> "ConfigObject":
        """Reads a toml file and converts it into a config object"""
        with open(toml_path, 'rb') as fh:
            loaded = toml_load(fh)
        return cls.__from_dictionary(loaded, include_env=include_env)

    @classmethod
    async def afrom_toml(cls, toml_path: Path, include_env: bool = False) -> "ConfigObject":
        """Reads a toml file and converts it into a config object, async"""
        async with aiofiles.open(toml_path, 'r') as fh:
            data = await fh.read()
        loaded = toml_loads(data)
        return cls.__from_dictionary(loaded, include_env=include_env)

    @classmethod
    def __from_dictionary(cls, loaded: dict[str, any], include_env: bool = False) -> "ConfigObject":
        def load_from_env(cls) -> dict[str, any]:
            loaded = {}
            env_base = f"{cls.schema()['title'].replace('Config', '')}"
            for key in cls.schema()['properties'].keys():
                env_key = f"{env_base}_{key}".upper()
                value = os.environ.get(env_key, None)
                if value:
                    loaded[key] = value
            return loaded

        errors = []
        kwargs = {}
        for key, schema_class in {
            "logging": LoggingConfig,
            "aprs": APRSConfig,
            "kiss": KissConfig,
            "location": LocationConfig,
            "mqtt": MQTTConfig
        }.items():
            env = load_from_env(schema_class) if include_env else {}
            env.update(loaded.get(key, {}))
            try:
                kwargs[key] = schema_class(**env)
            except ValidationError as exc:
                errors.append(exc)

        # combine all the separate validation exceptions into one
        if len(errors) > 0:
            # get the InitErrorDetails from the validation errors
            pydantic_errors = []
            for error in errors:
                pydantic_errors += error.errors()
            raise ValidationError.from_exception_data(title="mqtt2aprs config", line_errors=pydantic_errors)


        return cls(**kwargs)


@lru_cache
def get_config(config_path: str = DEFAULT_CONFIG_PATH, from_env: bool = False) -> ConfigObject:
    return ConfigObject.from_toml(config_path, from_env)


@alru_cache
async def aget_config(config_path: str = DEFAULT_CONFIG_PATH, from_env: bool = False) -> ConfigObject:
    return await ConfigObject.afrom_toml(config_path, from_env)
