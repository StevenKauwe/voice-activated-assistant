from typing import Tuple, Type
from enum import Enum
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from pydantic import Field


class LanguageModelType(str, Enum):
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    OPENAI = "openai"

class LanguageModelConfig(BaseSettings):
    model_id: str
    model_type: LanguageModelType
    server_url: str | None = Field("http://localhost:11434/v1") 

class ClipboardConfig(BaseSettings):
    copy_to_clipboard: bool
    copy_from_code_blocks: bool
    paste_at_cursor: bool
    

class Settings(BaseSettings):
    MODEL_ID_STT: str = "distil-whisper/distil-small.en"
    LLM_CONFIG: LanguageModelConfig = LanguageModelConfig()
    CLIPBOARD_CONFIG: ClipboardConfig = ClipboardConfig()
    MAX_AUDIO_LENGTH_SECONDS: int = 3600

    model_config = SettingsConfigDict(yaml_file="settings_config.yml")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)

    def update(self, attr_name: str, new_value):
        if hasattr(self, attr_name):
            setattr(self, attr_name, new_value)
        else:
            raise ValueError(f"No such attribute: {attr_name}")


config = Settings()
