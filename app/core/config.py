from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    max_agent_iterations: int = 10
    app_name: str = "AI Automation Pipeline"

    class Config:
        env_file = ".env"


settings = Settings()
