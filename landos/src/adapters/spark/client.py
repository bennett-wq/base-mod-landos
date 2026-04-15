"""Spark RESO Web API client — HTTP helpers for OData Property queries.

Extracted from scripts/ingest_spark_live.py so src/ code can query the
Spark API without depending on the scripts tree. Matches the existing
script's URL construction, Bearer-token auth, and error-handling pattern,
but raises structured exceptions instead of calling sys.exit.

This module is deliberately minimal: a single function
``fetch_active_land_listings`` that takes a scope (county / township / zip)
and returns the raw list of OData Property records. Parsing the records
into domain objects is the caller's responsibility.

Environment variables:
  SPARK_API_KEY   - Bearer token (required unless api_key= kwarg is passed)
  SPARK_BASE_URL  - OData base URL, defaults to the replication endpoint

Dependency injection for tests:
  The ``_urlopen`` kwarg allows tests to substitute a fake urlopen callable
  so no real HTTP traffic is generated. Tests MUST use this hook.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

DEFAULT_SPARK_BASE_URL = "https://replication.sparkapi.com/Reso/OData"

# Module-level env snapshot. Mirrors the outreach_drafter pattern: captured
# once at import time so handlers can monkeypatch the module attribute
# directly in tests without re-reading os.environ.
_ENV_API_KEY: str | None = os.environ.get("SPARK_API_KEY")
_ENV_BASE_URL: str | None = os.environ.get("SPARK_BASE_URL")


class SparkHTTPError(RuntimeError):
    """Raised when the Spark API returns a non-2xx response or is unreachable.

    Wraps the underlying urllib exception (or OSError / TimeoutError) so
    callers can distinguish "the API broke" from "we passed a bad scope."
    """


# Scope type → OData field name.
# Spark OData exposes CountyOrParish + City + PostalCode as filterable.
# Township names in Michigan overlap with City, so "township" maps to City
# until M3 introduces proper polygon/boundary matching.
_SCOPE_FIELD_MAP: dict[str, str] = {
    "county": "CountyOrParish",
    "township": "City",
    "zip": "PostalCode",
}


def fetch_active_land_listings(
    *,
    scope_type: str,
    scope_value: str,
    top: int = 100,
    api_key: str | None = None,
    base_url: str | None = None,
    _urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict]:
    """Fetch active Land listings from Spark OData, filtered by scope.

    Scope-to-field mapping (see ``_SCOPE_FIELD_MAP``):
      county    → ``CountyOrParish eq '<value>'``
      township  → ``City eq '<value>'``  (Spark exposes township names via City)
      zip       → ``PostalCode eq '<value>'``

    Args:
        scope_type: One of "county", "township", "zip".
        scope_value: The literal value to match (e.g. "Washtenaw", "48197").
        top: Max records to return. Spark supports up to ~200 per request.
        api_key: Overrides SPARK_API_KEY env var if provided.
        base_url: Overrides SPARK_BASE_URL env var if provided.
        _urlopen: Dependency-injected urlopen callable for tests. MUST match
            urllib.request.urlopen's signature (req, timeout=...).

    Returns:
        The raw list of OData Property records (one dict per listing).
        Empty list if Spark returns zero matches.

    Raises:
        EnvironmentError: api_key is None AND SPARK_API_KEY is unset. This
            exception is intentionally uncaught in the agent layer so the
            MCP handler can catch it once and return a structured _err.
        ValueError: scope_type is not in ``_SCOPE_FIELD_MAP``.
        SparkHTTPError: any urllib / network / JSON-decode failure.
    """
    resolved_key = api_key if api_key is not None else _ENV_API_KEY
    if not resolved_key:
        raise EnvironmentError(
            "SPARK_API_KEY is unset. Set the env var or pass api_key= explicitly."
        )
    resolved_base = base_url or _ENV_BASE_URL or DEFAULT_SPARK_BASE_URL

    if scope_type not in _SCOPE_FIELD_MAP:
        raise ValueError(
            f"Unsupported scope_type: {scope_type!r}. "
            f"Expected one of {sorted(_SCOPE_FIELD_MAP)}."
        )

    field = _SCOPE_FIELD_MAP[scope_type]
    # OData string literal escaping: single quote doubles to '' inside the
    # literal. Without this, any scope_value containing an apostrophe
    # (e.g. "O'Brien") would corrupt the filter and either return wrong
    # results or trigger an HTTP 400 from the Spark parser.
    escaped_value = str(scope_value).replace("'", "''")
    filters = [
        "PropertyType eq 'Land'",
        "StandardStatus eq 'Active'",
        f"{field} eq '{escaped_value}'",
    ]
    params = urllib.parse.urlencode(
        {
            "$filter": " and ".join(filters),
            "$top": top,
            "$orderby": "ModificationTimestamp desc",
        }
    )
    url = f"{resolved_base}/Property?{params}"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {resolved_key}",
            "Accept": "application/json",
        },
    )
    try:
        with _urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise SparkHTTPError(f"Spark API request failed: {exc}") from exc

    # Spark's OData response shape: {"value": [...]} (standard v4) or the
    # older {"D": {"Results": [...]}} envelope. Match whatever the existing
    # scripts/ingest_spark_live.py pattern accepts.
    return data.get("value", data.get("D", {}).get("Results", []))
