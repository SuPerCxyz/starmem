"""Secret-safe handling before sending user content to a remote provider."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretPattern:
    type: str
    pattern: re.Pattern[str]


_SECRET_PATTERNS = (
    SecretPattern(
        "credential",
        re.compile(r"(?i)(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s,;]+"),
    ),
    SecretPattern(
        "cloud_credential",
        re.compile(r"(?i)\b(?:access[_-]?key|secret[_-]?key|ak|sk)\s*[:=]\s*[^\s,;]+"),
    ),
    SecretPattern(
        "database_credential",
        re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb|redis)://[^\s]+"),
    ),
    SecretPattern("authorization", re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]+")),
    SecretPattern(
        "private_key",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    ),
    SecretPattern("cookie", re.compile(r"(?i)(cookie|set-cookie)\s*[:=]\s*[^\n]+")),
)


def redact_secrets(text: str) -> str:
    redacted = text
    for item in _SECRET_PATTERNS:
        redacted = item.pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def scan_secrets(text: str, *, max_findings: int = 64) -> list[dict[str, int | str]]:
    """Return only safe location/type summaries; matched values never leave this function."""
    findings: list[dict[str, int | str]] = []
    for item in _SECRET_PATTERNS:
        for match in item.pattern.finditer(text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            findings.append(
                {
                    "type": item.type,
                    "line": text.count("\n", 0, match.start()) + 1,
                    "column": match.start() - line_start + 1,
                }
            )
            if len(findings) >= max_findings:
                return findings
    return findings
