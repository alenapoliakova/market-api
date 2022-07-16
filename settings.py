from pydantic import BaseSettings


class Settings(BaseSettings):
    UVICORN_HOST: str
    UVICORN_PORT: int

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    class Config:
        env_file = '.env'


config = Settings()
