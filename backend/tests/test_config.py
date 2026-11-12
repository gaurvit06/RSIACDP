from types import SimpleNamespace
import base64
import unittest

from app.config import MAX_UPLOAD_BYTES_LIMIT, Settings, validate_access_token_settings, validate_bootstrap_codes, validate_correction_throttle_settings, validate_database_url, validate_upload_encryption, validate_upload_size, validate_web_origin


class CorrectionThrottleConfigurationTests(unittest.TestCase):
    def test_positive_correction_throttle_configuration_is_accepted(self):
        validate_correction_throttle_settings(SimpleNamespace(
            correction_max_requests=10,
            correction_window_seconds=900,
            correction_lockout_seconds=900,
        ))

    def test_each_nonpositive_correction_throttle_setting_fails_closed(self):
        for setting in (
            "correction_max_requests",
            "correction_window_seconds",
            "correction_lockout_seconds",
        ):
            values = {
                "correction_max_requests": 10,
                "correction_window_seconds": 900,
                "correction_lockout_seconds": 900,
            }
            values[setting] = 0
            with self.subTest(setting=setting), self.assertRaisesRegex(
                RuntimeError, "Correction throttling limits and durations must be positive integers"
            ):
                validate_correction_throttle_settings(SimpleNamespace(**values))


class BootstrapCodeConfigurationTests(unittest.TestCase):
    def test_distinct_long_bootstrap_codes_are_accepted(self):
        validate_bootstrap_codes(SimpleNamespace(
            initial_investigator_code="a" * 32,
            initial_reviewer_code="b" * 32,
        ))

    def test_bootstrap_codes_must_be_distinct_and_at_least_32_characters(self):
        cases = (
            ({"initial_investigator_code": "a" * 31, "initial_reviewer_code": "b" * 32}, "INITIAL_INVESTIGATOR_CODE"),
            ({"initial_investigator_code": "a" * 32, "initial_reviewer_code": "b" * 31}, "INITIAL_REVIEWER_CODE"),
            ({"initial_investigator_code": "a" * 32, "initial_reviewer_code": "a" * 32}, "must be different"),
        )
        for values, expected in cases:
            with self.subTest(expected=expected), self.assertRaisesRegex(RuntimeError, expected):
                validate_bootstrap_codes(SimpleNamespace(**values))


class RuntimeOriginConfigurationTests(unittest.TestCase):
    def test_access_token_lifetime_is_bounded(self):
        for minutes in (1, 60, 1440):
            with self.subTest(minutes=minutes):
                validate_access_token_settings(SimpleNamespace(token_minutes=minutes))
        for minutes in (0, -1, 1441):
            with self.subTest(minutes=minutes), self.assertRaisesRegex(RuntimeError, "ACCESS_TOKEN_MINUTES"):
                validate_access_token_settings(SimpleNamespace(token_minutes=minutes))

    def test_web_origin_accepts_origins_and_rejects_paths_credentials_and_wildcards(self):
        for origin in ("http://localhost:5173", "https://example.org", "https://example.org:8443"):
            with self.subTest(origin=origin):
                validate_web_origin(SimpleNamespace(web_origin=origin))
        for origin in (
            "",
            "*",
            "ftp://example.org",
            "https://example.org/",
            "https://example.org/path",
            "https://user:secret@example.org",
            "https://example.org?mode=unsafe",
            "https://example.org?",
            "https://example.org#",
            "https://example.org:",
            "https://example.org:70000",
            "https://example.org:443",
            "https://EXAMPLE.org",
            "https://münich.example.org",
            "https://bad host.example.org",
        ):
            with self.subTest(origin=origin), self.assertRaisesRegex(RuntimeError, "WEB_ORIGIN"):
                validate_web_origin(SimpleNamespace(web_origin=origin))


class UploadSizeConfigurationTests(unittest.TestCase):
    def test_supported_upload_size_range_matches_frontend_proxy_capacity(self):
        for size in (1, 10 * 1024 * 1024, MAX_UPLOAD_BYTES_LIMIT):
            with self.subTest(size=size):
                validate_upload_size(SimpleNamespace(max_upload_bytes=size))
        for size in (0, -1, MAX_UPLOAD_BYTES_LIMIT + 1):
            with self.subTest(size=size), self.assertRaisesRegex(RuntimeError, "MAX_UPLOAD_BYTES"):
                validate_upload_size(SimpleNamespace(max_upload_bytes=size))

    def test_upload_encryption_is_mandatory_outside_test_environment(self):
        validate_upload_encryption(SimpleNamespace(app_environment="testing", upload_encryption_key=""))
        valid_key = base64.b64encode(b"v" * 32).decode("ascii")
        validate_upload_encryption(SimpleNamespace(app_environment="development", upload_encryption_key=valid_key))
        with self.assertRaisesRegex(RuntimeError, "UPLOAD_ENCRYPTION_KEY"):
            validate_upload_encryption(SimpleNamespace(app_environment="production", upload_encryption_key=""))
        with self.assertRaisesRegex(RuntimeError, "UPLOAD_ENCRYPTION_KEY"):
            validate_upload_encryption(SimpleNamespace(app_environment="production", upload_encryption_key="invalid"))


class DatabaseConfigurationTests(unittest.TestCase):
    def test_postgresql_is_allowed_and_sqlite_is_test_only(self):
        validate_database_url(SimpleNamespace(
            database_url="postgresql+psycopg://user:password@db:5432/casework",
            app_environment="production",
        ))
        validate_database_url(SimpleNamespace(
            database_url="sqlite:///integration-test.db",
            app_environment="testing",
        ))

    def test_non_postgresql_runtime_urls_fail_with_clear_errors(self):
        cases = (
            ("sqlite:///production.db", "production", "SQLite is allowed only"),
            ("mysql+pymysql://user:secret@db/casework", "production", "must use PostgreSQL"),
            ("not a database url", "production", "valid SQLAlchemy database URL"),
        )
        for database_url, environment, expected in cases:
            with self.subTest(database_url=database_url), self.assertRaisesRegex(RuntimeError, expected) as caught:
                validate_database_url(SimpleNamespace(database_url=database_url, app_environment=environment))
            self.assertNotIn("secret", str(caught.exception))


class Neo4jConfigurationTests(unittest.TestCase):
    def test_render_private_hostname_builds_bolt_uri(self):
        config = Settings()
        config.neo4j_uri = ""
        config.neo4j_host = "rsiacdp-neo4j-ab12"

        self.assertEqual(config.effective_neo4j_uri, "bolt://rsiacdp-neo4j-ab12:7687")

    def test_explicit_local_uri_takes_precedence(self):
        config = Settings()
        config.neo4j_uri = "bolt://neo4j:7687"
        config.neo4j_host = "render-generated-host"

        self.assertEqual(config.effective_neo4j_uri, "bolt://neo4j:7687")


if __name__ == "__main__":
    unittest.main()
