from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_SECRETS = {"changeme", "secret", "your-secret-key", "supersecret", ""}


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:3000"
    DEBUG: bool = True
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_PUBLIC_URL: str = ""

    @model_validator(mode="after")
    def check_production_secrets(self) -> "Settings":
        if not self.DEBUG:
            if self.JWT_SECRET.lower() in _INSECURE_SECRETS:
                raise ValueError(
                    "JWT_SECRET no puede ser un valor por defecto en producción. "
                    "Configura una clave segura en las variables de entorno."
                )
            if len(self.JWT_SECRET) < 32:
                raise ValueError(
                    "JWT_SECRET debe tener al menos 32 caracteres en producción."
                )
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL es requerida.")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
