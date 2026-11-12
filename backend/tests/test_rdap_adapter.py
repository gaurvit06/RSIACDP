"""Offline RDAP adapter tests: no live public registry requests are made."""
import json
import socket
import unittest
from datetime import timezone
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.config import settings
from app.main import current_consent_version, validate_external_source_consent, CONSENT_VERSION, RDAP_CONSENT_VERSION
from app.source_adapters import RdapDomainAdapter


class RdapAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = RdapDomainAdapter()
        self.entity = SimpleNamespace(entity_type="domain", normalized_value="jobs.example.org")

    def test_domain_normalization_rejects_ip_and_bad_values(self):
        self.assertEqual(self.adapter._domain_ascii("Jobs.Example.Org."), "jobs.example.org")
        for value in ("127.0.0.1", "localhost", "https://example.org/path", "bad..example.org"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.adapter._domain_ascii(value)

    def test_bootstrap_uses_longest_suffix_and_only_https_services(self):
        registry = {"services": [
            [["org"], ["https://rdap.org.example/", "http://unsafe.example/"]],
            [["example.org"], ["https://specific.example/rdap/"]],
        ]}
        self.assertEqual(self.adapter._select_bases(registry, "jobs.example.org"), ("example.org", ["https://specific.example/rdap/"]))

    def test_registry_bases_reject_private_ip_literals_and_unsafe_url_parts(self):
        unsafe = (
            "http://rdap.example/",
            "https://127.0.0.1/",
            "https://[::1]/",
            "https://user:pass@rdap.example/",
            "https://rdap.example:8443/",
            "https://rdap.example/?target=internal",
            "https://rdap.example/#fragment",
            "https://rdap..example/",
            "https://-rdap.example/",
        )
        for base in unsafe:
            with self.subTest(base=base):
                self.assertFalse(self.adapter._safe_base(base))

    def test_rdap_host_resolution_rejects_private_and_mixed_public_private_answers(self):
        public = (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443))
        private = (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("10.0.0.8", 443))
        with patch("app.source_adapters.socket.getaddrinfo", return_value=[public]):
            self.assertEqual(self.adapter._resolve_public_address("rdap.example"), "93.184.216.34")
        for answers in ([private], [public, private]):
            with self.subTest(answers=answers), patch("app.source_adapters.socket.getaddrinfo", return_value=answers), self.assertRaisesRegex(ValueError, "non_public"):
                self.adapter._resolve_public_address("rdap.example")

    def test_pinned_rdap_request_uses_ip_for_connection_and_hostname_for_host_and_tls(self):
        public = (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 443))
        with httpx.Client(trust_env=False) as client, patch("app.source_adapters.socket.getaddrinfo", return_value=[public]):
            request = self.adapter._pinned_request(client, "https://rdap.example/rdap/domain/jobs.example.org")
        self.assertEqual(request.url.host, "93.184.216.34")
        self.assertEqual(request.headers["host"], "rdap.example")
        self.assertEqual(request.extensions["sni_hostname"], b"rdap.example")
        self.assertEqual(request.url.path, "/rdap/domain/jobs.example.org")

    def test_submitted_url_and_non_domain_entities_are_never_fetched(self):
        entities = (
            SimpleNamespace(entity_type="url", normalized_value="http://127.0.0.1/private"),
            SimpleNamespace(entity_type="email", normalized_value="recruiter@example.invalid"),
            SimpleNamespace(entity_type="phone", normalized_value="9876543210"),
        )
        with patch.object(self.adapter, "_fetch") as fetch:
            for entity in entities:
                with self.subTest(entity_type=entity.entity_type):
                    self.assertEqual(self.adapter.check(entity), [])
            fetch.assert_not_called()

    def test_domain_lookup_sends_only_normalized_domain_to_registry(self):
        registry = {"services": [[ ["org"], ["https://rdap.example/" ] ]]}
        entity = SimpleNamespace(entity_type="domain", normalized_value="Jobs.Example.Org.")
        with patch.object(self.adapter, "_bootstrap", return_value=(registry, "2026-10-20", "2026-10-21T00:00:00+00:00")), patch.object(
            self.adapter, "_fetch", return_value=(404, {}, b"{}")
        ) as fetch:
            self.adapter.check(entity)
        fetch.assert_called_once_with("https://rdap.example/domain/jobs.example.org")

    def test_404_is_neutral_empty_result(self):
        with patch.object(self.adapter, "_bootstrap", return_value=({"services": [[ ["org"], ["https://rdap.example/"] ]]}, "2026-10-20", "2026-10-21T00:00:00+00:00")), patch.object(self.adapter, "_fetch", return_value=(404, {}, b"{}")):
            item = self.adapter.check(self.entity)[0]
        self.assertEqual(item.outcome, "no_result")
        self.assertEqual(item.authority, "registry_data")
        self.assertIn("not evidence", item.excerpt)

    def test_redirect_is_unavailable_and_not_followed(self):
        with patch.object(self.adapter, "_bootstrap", return_value=({"services": [[ ["org"], ["https://rdap.example/"] ]]}, "2026-10-20", "2026-10-21T00:00:00+00:00")), patch.object(self.adapter, "_fetch", return_value=(302, {"location": "https://other.example/"}, b"")) as fetch:
            item = self.adapter.check(self.entity)[0]
        self.assertEqual(item.outcome, "unavailable")
        self.assertEqual(fetch.call_count, 1)

    def test_success_only_retains_minimized_non_contact_metadata_and_hash(self):
        record = {"objectClassName": "domain", "ldhName": "jobs.example.org", "events": [{"eventAction": "registration", "eventDate": "2020-01-01T00:00:00Z"}], "status": ["active"], "nameservers": [{"ldhName": "ns1.example.org"}], "entities": [{"vcardArray": ["vcard", [["fn", {}, "text", "PERSONAL CONTACT"]]]}]}
        body = json.dumps(record).encode()
        with patch.object(self.adapter, "_bootstrap", return_value=({"services": [[ ["org"], ["https://rdap.example/"] ]]}, "2026-10-20", "2026-10-21T00:00:00+00:00")), patch.object(self.adapter, "_fetch", return_value=(200, {}, body)):
            item = self.adapter.check(self.entity)[0]
        self.assertEqual(item.outcome, "result")
        self.assertIn("response_sha256", item.details)
        self.assertIn("registration", item.details["events"])
        self.assertNotIn("PERSONAL CONTACT", item.excerpt)
        self.assertEqual(item.retrieved_at.tzinfo, timezone.utc)


class ExternalConsentTests(unittest.TestCase):
    def test_policy_and_consent_are_versioned_and_explicit_only_when_enabled(self):
        previous = settings.rdap_enabled
        try:
            settings.rdap_enabled = False
            self.assertEqual(current_consent_version(), CONSENT_VERSION)
            validate_external_source_consent(CONSENT_VERSION, False)
            settings.rdap_enabled = True
            self.assertEqual(current_consent_version(), RDAP_CONSENT_VERSION)
            with self.assertRaises(Exception):
                validate_external_source_consent(CONSENT_VERSION, True)
            with self.assertRaises(Exception):
                validate_external_source_consent(RDAP_CONSENT_VERSION, False)
            validate_external_source_consent(RDAP_CONSENT_VERSION, True)
        finally:
            settings.rdap_enabled = previous


if __name__ == "__main__":
    unittest.main()
