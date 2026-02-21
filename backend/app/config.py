from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "lgtm"
    openai_api_key: Optional[str] = None
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
