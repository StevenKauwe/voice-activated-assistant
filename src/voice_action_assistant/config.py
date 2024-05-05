from enum import Enum
from typing import Tuple, Type

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class LanguageModelType(str, Enum):
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    OPENAI = "openai"


# nvim find and replace model_id with llm_id but case sensitive: %s/model_id/llm_id/g
class LanguageModelConfig(BaseSettings):
    model_id: str
    model_type: LanguageModelType
    server_url: str | None = Field("http://localhost:11434/v1")

    @classmethod
    def get_default_huggingface_config(cls):
        return cls(
            model_id="",
            model_type=LanguageModelType.HUGGINGFACE,
            server_url=None,
        )

    @classmethod
    def get_default_ollama_config(cls):
        return cls(
            model_id="llama3",
            model_type=LanguageModelType.OLLAMA,
            server_url="http://localhost:11434/v1",
        )

    @classmethod
    def get_default_openai_config(cls):
        return cls(
            model_id="gpt-4-turbo",
            model_type=LanguageModelType.OPENAI,
            server_url=None,
        )


class ClipboardConfig(BaseSettings):
    copy_to_clipboard: bool | None = Field(True)
    copy_from_code_blocks: bool | None = Field(True)
    paste_at_cursor: bool | None = Field(True)

    @classmethod
    def get_default(cls):
        return cls(
            copy_to_clipboard=True,
            copy_from_code_blocks=True,
            paste_at_cursor=True,
        )


class Settings(BaseSettings):
    CLIPBOARD_CONFIG: ClipboardConfig = ClipboardConfig.get_default()
    LLM_CONFIG: LanguageModelConfig = LanguageModelConfig.get_default_huggingface_config()
    MAX_AUDIO_LENGTH_SECONDS: int = 3600
    MODEL_ID_STT: str = "distil-whisper/distil-small.en"

    AUDIO_FILES_DIR: str = "src/audio_files"
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
        for _ in [init_settings, env_settings, dotenv_settings, file_secret_settings]:
            pass
        return (YamlConfigSettingsSource(settings_cls),)

    def update(self, attr_name: str, new_value):
        if hasattr(self, attr_name):
            setattr(self, attr_name, new_value)
        else:
            raise ValueError(f"No such attribute: {attr_name}")


config = Settings()
