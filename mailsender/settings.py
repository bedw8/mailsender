import sys
from enum import Enum
from typing import Annotated
from platformdirs.unix import Unix
from platformdirs import PlatformDirs
import warnings

from pydantic import (
    BaseModel,
    Field,
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


class GmailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="gmail__")

    credentials_file: Annotated[Path, Field(validate_default=True)] = "credentials.json"
    scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]
    port: int = 0

    def model_post_init(self, context):
        if not self.credentials_file.is_file():
            warnings.warn(
                f"{self.credentials_file} does not exists. Please add it or provide a credentials file path through the CREDENTIALS_FILE environment variable."
            )


class SenderSettings(BaseModel):
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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    config_dir: Path = dirs.user_config_path
    gmail: GmailSettings = Field(default_factory=GmailSettings)
    sender: SenderSettings = Field(default_factory=SenderSettings)
    db: DBSettings = Field(default_factory=DBSettings)

    runtime: AppRuntime = AppRuntime.script
    trackingURL: str = "localhost:8888"  # TODO: Cambiar

    # def model_post_init(self, context):
    #     creds_file = self.gmail.credentials_file
    #     print(creds_file)
    #     print(creds_file.parts)
    #     if len(creds_file.parts) == 1:
    #         self.gmail.credentials_file = self.config_dir / creds_file

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
            YamlConfigSettingsSource(settings_cls, yaml_file="config.yaml"),
        )

    @classmethod
    def load(cls) -> "Settings":
        return cls()

    def to_yaml(self, path: Path):
        import yaml

        print("Writing config file")
        yaml.dump(config.model_dump(mode="json"), Path(path).open("w"))


config = Settings()

# TODO: Change the following to api/main.py
# if not cfile.file.is_file():
#
#     print("Writing config file")
#     print(config)
#     yaml.dump(config.model_dump(mode="json"), cfile.file.open("w"))
