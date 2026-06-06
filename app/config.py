from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_app_token: str = ""
    slack_private_channel_id: str = ""
    groq_api_key: str = ""
    database_url: str = ""
    company_name: str = "Your Company"
    company_product: str = "Your Product"
    port: int = 8000
    node_env: str = "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
