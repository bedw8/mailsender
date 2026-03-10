import sys
from enum import Enum
from platformdirs.unix import Unix
from platformdirs import PlatformDirs
import warnings

from pydantic import (
    BaseModel,
    PostgresDsn,
    field_validator,
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


class GmailSettings(BaseModel):
    credentials_file: Path = "credentials.json"
    scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]
    port: int = 0


class SenderSettings(BaseSettings):
    max_emails: int = 100


class DBSettings(BaseModel):
    name: str = "accounts.db"
    records_db: PostgresDsn | None = None

    @field_validator("records_db")
    def check_db_name(cls, v):
        if v is not None:
            assert v.path and len(v.path) > 1, "database must be provided"
            return v


class AppRuntime(Enum):
    script = "script"
    uvicorn = "uvicorn"


def _is_default(self, attr):
    cls = self.__class__
    attrval = getattr(self, attr)
    return attrval == cls.model_fields.get(attr).default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")

    config_dir: Path = dirs.user_config_path
    gmail: GmailSettings = GmailSettings()
    sender: SenderSettings = SenderSettings()
    db: DBSettings = DBSettings()

    runtime: AppRuntime = AppRuntime.script
    trackingURL: str = "localhost:8888"  # TODO: Cambiar

    def model_post_init(self, context):
        creds_file = self.gmail.credentials_file
        if len(creds_file.parts) == 1:
            self.gmail.credentials_file = self.config_dir / creds_file

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


# TODO: Change the following to api/main.py

config = Settings()

# try:
if not config.credentials_file.is_file():
    warnings.warn(
        f"{config.credentials_file} does not exists. Please add it or provide a credentials file path through the CREDENTIALS_FILE environment variable."
    )

if not cfile.file.is_file():
    import yaml

    print("Writing config file")
    print(config)
    yaml.dump(config.model_dump(mode="json"), cfile.file.open("w"))
