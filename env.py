from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_name: str = 'Bridge'

    mongodb_host: str = 'localhost'
    mongodb_port: int = 27017

    log_level: str = 'INFO'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
