from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = 'bridge-bot'
    display_name: str = 'Connecty'

    discord_api_token: str

    mongodb_host: str
    mongodb_port: int

    manager_usernames: list[str] = ['nikitacometa']

    log_level: str = 'INFO'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
