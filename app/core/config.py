from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from urllib.parse import quote_plus


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="FastAPI + MariaDB CRUD")
    app_env: str = Field(default="dev")
    debug: bool = Field(default=True)

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=3306)
    db_name: str = Field(default="fastapi_crud")
    db_user: str = Field(default="root")
    db_password: str = Field(default="")

    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    @property
    def database_url(self) -> str:
        user = quote_plus(self.db_user)
        pwd = quote_plus(self.db_password)
        host = self.db_host
        return f"mysql+pymysql://{user}:{pwd}@{host}:{self.db_port}/{self.db_name}?charset=utf8mb4"


settings = Settings()
