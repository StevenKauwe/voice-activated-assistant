from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class Settings(BaseSettings):
    MODEL_ID: str = "gpt-4-turbo"
    COPY_TO_CLIPBOARD: bool = True
    EXTRACT_CODE_BLOCKS: bool = True
    LOCAL: bool = True
    MAX_AUDIO_LENGTH_SECONDS: int = 3600
    USE_TTS: bool = False
    AUDIO_SPEED: float = 1.25
    AUDIO_FILES_DIR: str = "src/audio_files"
    LLM_ACTION_PROMPTS_DIR: str = "src/llm-action-prompts"
    PASTE_AT_CURSOR: bool = False

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
