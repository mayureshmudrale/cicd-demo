import json

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://ideaboard:ideaboard@localhost:5432/ideaboard"
    otel_exporter_otlp_endpoint: str = "http://otel-lgtm:4317"
    otel_service_name: str = "idea-board-backend"

    # backend/faults.py reads these to decide how (and whether) to misbehave.
    # Canary-only: set via the Rollout's canary-specific Helm values, never
    # on the stable track.
    fault_mode: str = "none"
    fault_rate: float = 1.0
    fault_latency_ms: int = 3000
    fault_cpu_burn_ms: int = 2000

    model_config = {"env_file": ".env"}


settings = Settings()
