from ...config import TranslatorConfig
from ...config import ConfigObject


class Translator:
    def __init__(self, translator_config: TranslatorConfig, service_config: ConfigObject) -> None:
        self._type = translator_config.type
        self._translator_config = translator_config.config
        self._service_config = service_config
