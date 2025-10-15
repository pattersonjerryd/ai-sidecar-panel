from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Sidecar Panel"
    simulate: bool = True
    class Config:
        env_prefix = "SIDECAR_"
        env_file = ".env"
settings = Settings()
