from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "satpam_dev_2024"
    secret_key: str = "dev-secret-key-satpam-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS: origin frontend yang diizinkan (pisahkan dengan koma di .env).
    # Default mencakup Vite dev server lokal (localhost & 127.0.0.1, port 5173).
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()