"""Strips likely secret material out of text before it is sent to Gemini.

Defense in depth only: callers are expected to pass synthetic data (traces,
logs, diffs) in the first place. This catches what slips through — a stray
token pasted into a log line, a leaked key in a code snippet under review.
"""
import re

_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                                   # AWS access key id
    re.compile(r"(?i)aws_secret_access_key\s*=\s*\S+"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),                       # Slack tokens
    re.compile(r"ghp_[0-9A-Za-z]{36}"),                                 # GitHub PAT
    re.compile(r"gh[oprsu]_[0-9A-Za-z]{36}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.DOTALL),
    re.compile(r"eyJ[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}"),  # JWT-shaped
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[A-Za-z0-9/+_.-]{8,}['\"]?"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{10,}"),
]

_REDACTED = "[REDACTED]"


def redact(text: str) -> str:
    for pattern in _PATTERNS:
        text = pattern.sub(_REDACTED, text)
    return text
