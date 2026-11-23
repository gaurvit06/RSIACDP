import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from sqlalchemy.engine import make_url

MAX_UPLOAD_BYTES_LIMIT = 50 * 1024 * 1024


class Settings:
    official_job_boards: str = os.getenv("OFFICIAL_JOB_BOARDS", "")
    app_environment: str = os.getenv("APP_ENV", "production").strip().lower()
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://recruitment_intel:change-this-local-password@localhost:5432/recruitment_intel")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "./uploads")).resolve()
    upload_encryption_key: str = os.getenv("UPLOAD_ENCRYPTION_KEY", "")
    upload_storage_backend: str = os.getenv("UPLOAD_STORAGE_BACKEND", "local").strip().lower()
    supabase_url: str = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_storage_bucket: str = os.getenv("SUPABASE_STORAGE_BUCKET", "private-evidence")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", "10485760"))
    retention_days: int = int(os.getenv("DATA_RETENTION_DAYS", "180"))
    login_max_attempts: int = int(os.getenv("LOGIN_MAX_ATTEMPTS", "8"))
    login_window_seconds: int = int(os.getenv("LOGIN_WINDOW_SECONDS", "900"))
    login_lockout_seconds: int = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))
    register_max_requests: int = int(os.getenv("REGISTER_MAX_REQUESTS", "20"))
    register_window_seconds: int = int(os.getenv("REGISTER_WINDOW_SECONDS", "900"))
    register_lockout_seconds: int = int(os.getenv("REGISTER_LOCKOUT_SECONDS", "900"))
    correction_max_requests: int = int(os.getenv("CORRECTION_MAX_REQUESTS", "10"))
    correction_window_seconds: int = int(os.getenv("CORRECTION_WINDOW_SECONDS", "900"))
    correction_lockout_seconds: int = int(os.getenv("CORRECTION_LOCKOUT_SECONDS", "900"))
    password_reset_token_minutes: int = int(os.getenv("PASSWORD_RESET_TOKEN_MINUTES", "20"))
    rdap_enabled: bool = os.getenv("RDAP_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    rdap_timeout_seconds: float = float(os.getenv("RDAP_TIMEOUT_SECONDS", "5"))
    rdap_max_response_bytes: int = int(os.getenv("RDAP_MAX_RESPONSE_BYTES", "1048576"))
    run_inline_worker: bool = os.getenv("RUN_INLINE_WORKER", "false").strip().lower() in {"1", "true", "yes", "on"}
    web_origin: str = os.getenv("WEB_ORIGIN", "http://localhost:5173")
    initial_investigator_code: str = os.getenv("INITIAL_INVESTIGATOR_CODE", "")
    initial_reviewer_code: str = os.getenv("INITIAL_REVIEWER_CODE", "")
    campaign_link_threshold: int = int(os.getenv("CAMPAIGN_LINK_THRESHOLD", "40"))
    neo4j_uri: str = os.getenv("NEO4J_URI", "")
    neo4j_host: str = os.getenv("NEO4J_HOST", "").strip()
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    neo4j_password_slash_safe: bool = os.getenv("NEO4J_PASSWORD_SLASH_SAFE", "false").strip().lower() in {"1", "true", "yes", "on"}

    @property
    def effective_neo4j_uri(self) -> str:
        # Render supplies the private service's generated hostname through
        # fromService; local Compose continues to use its explicit NEO4J_URI.
        if self.neo4j_uri:
            return self.neo4j_uri
        return f"bolt://{self.neo4j_host}:7687" if self.neo4j_host else ""

    @property
    def effective_neo4j_password(self) -> str:
        # Neo4j's Docker image reserves '/' in NEO4J_AUTH; Render generates
        # base64 secrets and enables the same mapping in its entrypoint.
        return self.neo4j_password.replace("/", "_") if self.neo4j_password_slash_safe else self.neo4j_password


def validate_correction_throttle_settings(config: Settings) -> None:
    values = (
        config.correction_max_requests,
        config.correction_window_seconds,
        config.correction_lockout_seconds,
    )
    if any(value < 1 for value in values):
        raise RuntimeError("Correction throttling limits and durations must be positive integers")


def validate_bootstrap_codes(config: Settings) -> None:
    investigator = config.initial_investigator_code
    reviewer = config.initial_reviewer_code
    if not investigator or investigator.startswith("change-this"):
        raise RuntimeError("Set INITIAL_INVESTIGATOR_CODE to a private one-time setup value before starting the API")
    if not reviewer or reviewer.startswith("change-this"):
        raise RuntimeError("Set INITIAL_REVIEWER_CODE to a different private one-time setup value before starting the API")
    if len(investigator) < 32:
        raise RuntimeError("INITIAL_INVESTIGATOR_CODE must contain at least 32 characters")
    if len(reviewer) < 32:
        raise RuntimeError("INITIAL_REVIEWER_CODE must contain at least 32 characters")
    if investigator == reviewer:
        raise RuntimeError("INITIAL_INVESTIGATOR_CODE and INITIAL_REVIEWER_CODE must be different values")


def validate_access_token_settings(config: Settings) -> None:
    if not 1 <= config.token_minutes <= 1440:
        raise RuntimeError("ACCESS_TOKEN_MINUTES must be between 1 and 1440")


def validate_upload_size(config: Settings) -> None:
    if not 1 <= config.max_upload_bytes <= MAX_UPLOAD_BYTES_LIMIT:
        raise RuntimeError(f"MAX_UPLOAD_BYTES must be between 1 and {MAX_UPLOAD_BYTES_LIMIT}")


def validate_upload_encryption(config: Settings) -> None:
    """Require encrypted original-file storage outside isolated test environments."""
    if config.app_environment == "testing":
        return
    from .private_storage import decode_upload_encryption_key
    try:
        key = decode_upload_encryption_key(config.upload_encryption_key)
    except ValueError:
        raise RuntimeError("UPLOAD_ENCRYPTION_KEY must be canonical base64 for exactly 32 bytes")
    if key is None:
        raise RuntimeError("Set UPLOAD_ENCRYPTION_KEY to a private base64-encoded 32-byte key before starting API or worker")


def validate_upload_storage(config: Settings) -> None:
    """Fail startup on unsupported or incomplete shared private-storage configuration."""
    if config.upload_storage_backend == "local":
        return
    if config.upload_storage_backend != "supabase":
        raise RuntimeError("UPLOAD_STORAGE_BACKEND must be either local or supabase")
    try:
        parsed = urlsplit(config.supabase_url)
        _ = parsed.port
    except ValueError:
        raise RuntimeError("SUPABASE_URL must be a valid HTTPS project origin")
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise RuntimeError("SUPABASE_URL must be a valid HTTPS project origin")
    if not config.supabase_service_role_key or len(config.supabase_service_role_key) < 20:
        raise RuntimeError("Set SUPABASE_SERVICE_ROLE_KEY in the API and worker secret stores")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]", config.supabase_storage_bucket):
        raise RuntimeError("SUPABASE_STORAGE_BUCKET must be a valid bucket name")


def validate_web_origin(config: Settings) -> None:
    value = config.web_origin
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except (AttributeError, ValueError):
        raise RuntimeError("WEB_ORIGIN must be a valid HTTP(S) origin without credentials, path, query, or fragment")
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or not parsed.netloc
        or parsed.netloc.endswith(":")
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != ""
        or parsed.query
        or parsed.fragment
        or "?" in value
        or "#" in value
        or "*" in parsed.netloc
        or value != value.lower()
        or not parsed.netloc.isascii()
        or any(character.isspace() for character in value)
        or (port is not None and not 1 <= port <= 65535)
        or (parsed.scheme == "http" and port == 80)
        or (parsed.scheme == "https" and port == 443)
    ):
        raise RuntimeError("WEB_ORIGIN must be a valid HTTP(S) origin without credentials, path, query, or fragment")


def validate_database_url(config: Settings) -> None:
    try:
        backend = make_url(config.database_url).get_backend_name()
    except Exception:
        raise RuntimeError("DATABASE_URL must be a valid SQLAlchemy database URL")
    if backend == "sqlite" and config.app_environment == "testing":
        return
    if backend != "postgresql":
        raise RuntimeError("DATABASE_URL must use PostgreSQL; SQLite is allowed only when APP_ENV=testing")

settings = Settings()
