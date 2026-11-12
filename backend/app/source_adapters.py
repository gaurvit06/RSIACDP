"""Structured evidence-source adapters. PostgreSQL remains the record of findings."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Protocol
from urllib.parse import quote, urlsplit

import httpx

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Entity, SourceRecord


@dataclass(frozen=True)
class SourceObservation:
    source_name: str
    source_type: str
    source_ref: str
    claim: str
    outcome: str
    excerpt: str
    authority: str
    retrieved_at: datetime
    details: dict


class EvidenceSourceAdapter(Protocol):
    """One configured source that returns persisted, provenance-bearing observations."""

    name: str
    adapter_version: str

    def check(self, entity: Entity) -> list[SourceObservation]: ...


class LocalEvidenceCorpusAdapter:
    """Exact normalized-identifier checks against persisted and bundled local records."""

    name = "Curated local evidence corpus"
    adapter_version = "local-corpus-v1"

    def __init__(self, db: Session, static_corpus_path: Path | None = None):
        self.db = db
        self.static_corpus_path = static_corpus_path or Path(__file__).with_name("evidence_corpus.json")

    def check(self, entity: Entity) -> list[SourceObservation]:
        now = datetime.now(timezone.utc)
        fingerprint = hashlib.sha256(f"{entity.entity_type}:{entity.normalized_value}".encode("utf-8")).hexdigest()
        records: list[SourceObservation] = []
        persisted = self.db.scalars(select(SourceRecord).where(
            SourceRecord.entity_type == entity.entity_type,
            SourceRecord.normalized_value == entity.normalized_value,
            SourceRecord.active.is_(True),
        ).with_for_update()).all()
        for record in persisted:
            records.append(SourceObservation(
                source_name=record.source_name,
                source_type="curated_local_corpus",
                source_ref=record.record_id,
                claim=record.claim,
                outcome=record.outcome,
                excerpt=record.excerpt,
                authority=record.authority,
                retrieved_at=now,
                details={
                    "matched_entity_type": entity.entity_type,
                    "matched_normalized_value": entity.normalized_value,
                    "entity_fingerprint": fingerprint,
                    "corpus_version": self.adapter_version,
                    "source_category": record.source_type,
                    "source_record_ref": record.source_ref,
                    "source_record_retrieved_at": record.retrieved_at.isoformat(),
                    "lookup": "exact_normalized_identifier",
                },
            ))

        if self.static_corpus_path.exists():
            corpus = json.loads(self.static_corpus_path.read_text(encoding="utf-8"))
            for record in corpus.get("records", []):
                if (record.get("entity_type"), record.get("normalized_value")) != (entity.entity_type, entity.normalized_value):
                    continue
                source_ref = record.get("record_id")
                if not source_ref:
                    raise ValueError("Every bundled local evidence record must have a record_id")
                records.append(SourceObservation(
                    source_name=record["source_name"],
                    source_type="curated_local_corpus",
                    source_ref=source_ref,
                    claim=record["claim"],
                    outcome=record.get("outcome", "result"),
                    excerpt=record.get("excerpt", ""),
                    authority=record.get("authority", "unverified_public_report"),
                    retrieved_at=now,
                    details={
                        "matched_entity_type": entity.entity_type,
                        "matched_normalized_value": entity.normalized_value,
                        "entity_fingerprint": fingerprint,
                        "corpus_version": record.get("corpus_version", "unversioned"),
                        "source_record_ref": record.get("source_ref", ""),
                        "lookup": "exact_normalized_identifier",
                    },
                ))

        # If the same source record exists in the database and bundled seed corpus,
        # persist it only once for this lookup.
        unique: dict[str, SourceObservation] = {item.source_ref: item for item in records}
        if unique:
            return list(unique.values())

        return [SourceObservation(
            source_name=self.name,
            source_type="curated_local_corpus",
            source_ref=f"{self.adapter_version}:no-result:{fingerprint}",
            claim=f"No curated local corpus record matched this {entity.entity_type} identifier",
            outcome="no_result",
            excerpt="No matching record is present in the configured local corpus. An empty result is not evidence of fraud or legitimacy.",
            authority="curated",
            retrieved_at=now,
            details={
                "matched_entity_type": entity.entity_type,
                "entity_fingerprint": fingerprint,
                "corpus_version": self.adapter_version,
                "lookup": "exact_normalized_identifier",
            },
        )]


RDAP_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
RDAP_ADAPTER_VERSION = "iana-rdap-domain-v2-dns-pinned"
_BOOTSTRAP_LOCK = Lock()
_BOOTSTRAP_CACHE: tuple[float, dict, str, str] | None = None


class RdapDomainAdapter:
    """Optional public RDAP lookup using IANA's DNS bootstrap registry.

    It uses only HTTPS URLs listed in the IANA registry, resolves and pins a
    globally routable address for each connection, preserves the original TLS
    hostname for certificate verification, never follows redirects, disables
    environment proxies, bounds responses, and never sends the original
    submitted URL to an RDAP server. The local evidence corpus remains independent.
    """

    name = "Public RDAP domain registration"
    adapter_version = RDAP_ADAPTER_VERSION

    def __init__(self, timeout_seconds: float = 5.0, max_response_bytes: int = 1_048_576):
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes

    @staticmethod
    def _domain_ascii(value: str) -> str:
        domain = value.rstrip(".").strip().lower()
        if not domain or len(domain) > 253 or any(ch in domain for ch in "/:@?#"):
            raise ValueError("invalid_domain")
        try:
            ipaddress.ip_address(domain)
        except ValueError:
            pass
        else:
            raise ValueError("ip_literal")
        domain = domain.encode("idna").decode("ascii").lower()
        labels = domain.split(".")
        if len(labels) < 2 or any(
            not label
            or len(label) > 63
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
            for label in labels
        ):
            raise ValueError("invalid_domain")
        return domain

    @staticmethod
    def _resolve_public_address(hostname: str) -> str:
        """Resolve once, reject non-public answers, and return a pinned address.

        The caller connects to this IP while retaining the original hostname in
        the HTTP Host header and TLS SNI. Resolving again inside the HTTP client
        would reintroduce a DNS-rebinding window, so the request URL is rewritten
        to the selected address before it is sent.
        """
        try:
            answers = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError("rdap_host_resolution_failed") from exc
        addresses: list[str] = []
        for answer in answers:
            raw = answer[4][0]
            address = ipaddress.ip_address(raw.split("%", 1)[0])
            if not address.is_global or address.is_multicast or address.is_unspecified:
                raise ValueError("rdap_host_resolved_to_non_public_address")
            canonical = str(address)
            if canonical not in addresses:
                addresses.append(canonical)
        if not addresses:
            raise ValueError("rdap_host_has_no_address")
        return addresses[0]

    @classmethod
    def _pinned_request(cls, client: httpx.Client, url: str) -> httpx.Request:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.port not in {None, 443}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("unsafe_rdap_request_url")
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
        address = cls._resolve_public_address(hostname)
        request_host = f"[{address}]" if ":" in address else address
        pinned_url = parsed._replace(netloc=request_host).geturl()
        return client.build_request(
            "GET",
            pinned_url,
            headers={"Accept": "application/rdap+json, application/json", "Host": hostname},
            extensions={"sni_hostname": hostname.encode("ascii")},
        )

    def _fetch(self, url: str) -> tuple[int, dict[str, str], bytes]:
        timeout = httpx.Timeout(self.timeout_seconds, connect=self.timeout_seconds)
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            request = self._pinned_request(client, url)
            with client.send(request, stream=True) as response:
                size_header = response.headers.get("Content-Length")
                if size_header and size_header.isdigit() and int(size_header) > self.max_response_bytes:
                    raise ValueError("response_too_large")
                chunks = bytearray()
                for chunk in response.iter_bytes():
                    if len(chunks) + len(chunk) > self.max_response_bytes:
                        raise ValueError("response_too_large")
                    chunks.extend(chunk)
                return response.status_code, dict(response.headers), bytes(chunks)

    @staticmethod
    def _cache_lifetime(headers: dict[str, str]) -> int:
        cache_control = headers.get("cache-control", "")
        match = re.search(r"(?:^|,)\s*max-age=(\d+)", cache_control, re.IGNORECASE)
        if match:
            return max(60, min(int(match.group(1)), 86_400))
        expires = headers.get("expires")
        if expires:
            try:
                seconds = int((parsedate_to_datetime(expires) - datetime.now(timezone.utc)).total_seconds())
                return max(60, min(seconds, 86_400))
            except (TypeError, ValueError, OverflowError):
                pass
        return 21_600

    def _bootstrap(self) -> tuple[dict, str, str]:
        global _BOOTSTRAP_CACHE
        with _BOOTSTRAP_LOCK:
            if _BOOTSTRAP_CACHE and monotonic() < _BOOTSTRAP_CACHE[0]:
                return _BOOTSTRAP_CACHE[1], _BOOTSTRAP_CACHE[2], _BOOTSTRAP_CACHE[3]
            status, headers, body = self._fetch(RDAP_BOOTSTRAP_URL)
            if status != 200:
                raise RuntimeError(f"bootstrap_http_{status}")
            document = json.loads(body)
            if not isinstance(document, dict) or not isinstance(document.get("services"), list):
                raise ValueError("invalid_bootstrap")
            retrieved_at = datetime.now(timezone.utc).isoformat()
            publication = str(document.get("publication", "unknown"))[:80]
            _BOOTSTRAP_CACHE = (monotonic() + self._cache_lifetime(headers), document, publication, retrieved_at)
            return document, publication, retrieved_at

    @staticmethod
    def _select_bases(document: dict, domain: str) -> tuple[str, list[str]] | None:
        matches: list[tuple[int, str, list[str]]] = []
        for service in document.get("services", []):
            if not isinstance(service, list) or len(service) != 2:
                continue
            suffixes, bases = service
            if not isinstance(suffixes, list) or not isinstance(bases, list):
                continue
            for suffix in suffixes:
                if not isinstance(suffix, str):
                    continue
                normalized_suffix = suffix.strip().rstrip(".").lower()
                if normalized_suffix and (domain == normalized_suffix or domain.endswith("." + normalized_suffix)):
                    safe_bases = [base for base in bases if isinstance(base, str) and RdapDomainAdapter._safe_base(base)]
                    if safe_bases:
                        matches.append((len(normalized_suffix.split(".")), normalized_suffix, safe_bases))
        if not matches:
            return None
        _, suffix, bases = max(matches, key=lambda item: item[0])
        return suffix, bases

    @staticmethod
    def _safe_base(base: str) -> bool:
        try:
            parsed = urlsplit(base)
            if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
                return False
            if parsed.port not in {None, 443} or parsed.query or parsed.fragment:
                return False
            hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
            try:
                ipaddress.ip_address(hostname)
                return False
            except ValueError:
                pass
            labels = hostname.split(".")
            valid_hostname = len(hostname) <= 253 and len(labels) >= 2 and all(
                label and len(label) <= 63 and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
                for label in labels
            )
            return valid_hostname and hostname not in {"localhost", "localhost.localdomain"} and ".." not in parsed.path
        except (UnicodeError, ValueError):
            return False

    def _observation(
        self, entity: Entity, outcome: str, source_ref: str, claim: str, excerpt: str, details: dict
    ) -> SourceObservation:
        return SourceObservation(
            source_name=self.name,
            source_type="rdap_registry",
            source_ref=source_ref,
            claim=claim,
            outcome=outcome,
            excerpt=excerpt,
            authority="registry_data",
            retrieved_at=datetime.now(timezone.utc),
            details={
                **details,
                "matched_entity_type": entity.entity_type,
                "matched_normalized_value": entity.normalized_value,
                "entity_fingerprint": hashlib.sha256(f"{entity.entity_type}:{entity.normalized_value}".encode("utf-8")).hexdigest(),
                "adapter_version": self.adapter_version,
            },
        )

    def check(self, entity: Entity) -> list[SourceObservation]:
        if entity.entity_type != "domain":
            return []
        base_details = {"bootstrap_url": RDAP_BOOTSTRAP_URL, "lookup": "IANA_RFC9224_domain_bootstrap"}
        try:
            domain = self._domain_ascii(entity.normalized_value)
        except ValueError as exc:
            return [self._observation(entity, "error", RDAP_BOOTSTRAP_URL, "RDAP domain check could not validate this domain candidate", "The candidate was not a valid public DNS name for an RDAP lookup.", {**base_details, "failure_class": str(exc)[:40]})]

        try:
            document, publication, bootstrap_retrieved_at = self._bootstrap()
        except Exception as exc:
            return [self._observation(entity, "unavailable", RDAP_BOOTSTRAP_URL, "RDAP bootstrap registry could not be checked", "The IANA RDAP bootstrap lookup failed or returned an invalid response. This is not a negative domain result.", {**base_details, "failure_class": type(exc).__name__})]

        selected = self._select_bases(document, domain)
        if not selected:
            return [self._observation(entity, "unavailable", RDAP_BOOTSTRAP_URL, f"No RDAP service was mapped for {domain}", "The IANA bootstrap registry did not provide an HTTPS RDAP service for this domain suffix; no domain lookup was completed.", {**base_details, "bootstrap_publication": publication, "bootstrap_retrieved_at": bootstrap_retrieved_at})]
        suffix, bases = selected
        endpoint = bases[0].rstrip("/") + "/domain/" + quote(domain, safe=".-")
        details = {**base_details, "bootstrap_publication": publication, "bootstrap_retrieved_at": bootstrap_retrieved_at, "matched_bootstrap_suffix": suffix}
        try:
            status, headers, body = self._fetch(endpoint)
        except Exception as exc:
            return [self._observation(entity, "unavailable", endpoint, f"RDAP lookup could not be completed for {domain}", "The registry service could not be reached or returned a response outside the configured limits. This is not a negative result.", {**details, "failure_class": type(exc).__name__})]

        digest = hashlib.sha256(body).hexdigest()
        details = {**details, "response_sha256": digest, "http_status": status}
        if status == 404:
            return [self._observation(entity, "no_result", endpoint, f"RDAP returned no registration record for {domain}", "The mapped RDAP registry returned HTTP 404. This empty result is not evidence of fraud or legitimacy.", details)]
        if status == 429 or status >= 500 or 300 <= status < 400:
            return [self._observation(entity, "unavailable", endpoint, f"RDAP lookup was unavailable for {domain}", "The RDAP server rate-limited, redirected, or failed this lookup. No negative inference is made.", details)]
        if status != 200:
            return [self._observation(entity, "error", endpoint, f"RDAP lookup returned HTTP {status} for {domain}", "The registry did not return a usable domain record. No adverse conclusion is drawn.", details)]
        try:
            record = json.loads(body)
            returned_domain = self._domain_ascii(str(record.get("ldhName", "")))
            if record.get("objectClassName") != "domain" or returned_domain != domain:
                raise ValueError("response_domain_mismatch")
        except Exception as exc:
            return [self._observation(entity, "error", endpoint, f"RDAP response was not a matching domain record for {domain}", "The RDAP response could not be validated as a record for the requested domain.", {**details, "failure_class": type(exc).__name__})]

        events = {}
        for event in record.get("events", []):
            if isinstance(event, dict) and event.get("eventAction") in {"registration", "last changed", "expiration"}:
                value = str(event.get("eventDate", ""))[:40]
                if value:
                    events[str(event["eventAction"])] = value
        statuses = sorted({str(item)[:80] for item in record.get("status", [])[:30] if isinstance(item, str)}) if isinstance(record.get("status"), list) else []
        nameservers = sorted({str(item.get("ldhName", ""))[:253].lower() for item in record.get("nameservers", [])[:30] if isinstance(item, dict) and item.get("ldhName")}) if isinstance(record.get("nameservers"), list) else []
        safe_record = {"domain": domain, "events": events, "statuses": statuses, "nameservers": nameservers}
        excerpt = json.dumps(safe_record, ensure_ascii=True, sort_keys=True)
        details.update(safe_record)
        return [self._observation(entity, "result", endpoint, f"Public RDAP registry returned registration metadata for {domain}", excerpt[:2000], details)]
