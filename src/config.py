import sys
from platformdirs.unix import Unix
from platformdirs import PlatformDirs

from typing import Any, ClassVar
from pydantic import (
    BaseModel,
    computed_field,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from pathlib import Path

_APPNAME = "mailsender"


def directories():
    appname = _APPNAME
    if sys.platform == "darwin":
        # Force ~/ paths on macOS
        return Unix(appname=appname, appauthor=False)
    else:
        return PlatformDirs(appname=appname)


dirs = directories()


class ConfigFile(BaseSettings):
    file: Path | None = "config.yaml"  # YAML


cfile = ConfigFile()


class SenderSettings(BaseModel):
    scopes: list[str] = ["https://www.googleapis.com/auth/gmail.send"]
    max_emails: int = 100
    port: int = 0


class DBSettings(BaseModel):
    name: str = "accounts.db"


def _is_default(self, attr):
    cls = self.__class__
    attrval = getattr(self, attr)
    return attrval == cls.model_fields.get(attr).default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")

    config_dir: Path = dirs.user_config_path
    credentials_file: Path = config_dir / "credentials.json"

    def model_post_init(self, context):
        if not _is_default(self, "config_dir") and _is_default(
            self, "credentials_file"
        ):
            self.credentials_file = self.config_dir / "credentials.json"

    sender: SenderSettings = SenderSettings()
    db: DBSettings = DBSettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=["config.yaml"]),
            file_secret_settings,
            dotenv_settings,
        )


cfg = Settings()
