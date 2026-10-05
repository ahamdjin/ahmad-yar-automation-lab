"""Guard model-selected URLs before a server-side fetch to reduce SSRF risk."""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class UrlDecision:
    allowed: bool
    normalized_url: str | None
    reason: str
    resolved_ips: tuple[str, ...] = ()


def _unsafe_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return any((
        ip.is_private,
        ip.is_loopback,
        ip.is_link_local,
        ip.is_multicast,
        ip.is_reserved,
        ip.is_unspecified,
    ))


def evaluate_url(url: str, *, allow_http: bool = False, resolve_dns: bool = False) -> UrlDecision:
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return UrlDecision(False, None, "invalid_url")

    allowed_schemes = {"https", "http"} if allow_http else {"https"}
    if parts.scheme.lower() not in allowed_schemes:
        return UrlDecision(False, None, "scheme_not_allowed")

    if not parts.hostname:
        return UrlDecision(False, None, "missing_host")

    if parts.username or parts.password:
        return UrlDecision(False, None, "embedded_credentials_not_allowed")

    host = parts.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return UrlDecision(False, None, "localhost_not_allowed")

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return UrlDecision(False, None, "invalid_hostname")

    resolved: list[str] = []
    try:
        ipaddress.ip_address(ascii_host)
        if _unsafe_ip(ascii_host):
            return UrlDecision(False, None, "non_public_ip_not_allowed", (ascii_host,))
        resolved.append(ascii_host)
    except ValueError:
        if resolve_dns:
            try:
                infos = socket.getaddrinfo(
                    ascii_host,
                    parts.port or (443 if parts.scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            except socket.gaierror:
                return UrlDecision(False, None, "dns_resolution_failed")

            seen = []
            for info in infos:
                address = info[4][0]
                if address not in seen:
                    seen.append(address)

            for address in seen:
                try:
                    if _unsafe_ip(address):
                        return UrlDecision(False, None, "dns_resolved_to_non_public_ip", tuple(seen))
                except ValueError:
                    return UrlDecision(False, None, "dns_returned_invalid_ip", tuple(seen))
            resolved.extend(seen)

    try:
        port = parts.port
    except ValueError:
        return UrlDecision(False, None, "invalid_port")

    netloc = ascii_host
    if ":" in ascii_host and not ascii_host.startswith("["):
        netloc = f"[{ascii_host}]"

    default_port = 443 if parts.scheme.lower() == "https" else 80
    if port and port != default_port:
        netloc = f"{netloc}:{port}"

    normalized = urlunsplit((
        parts.scheme.lower(),
        netloc,
        parts.path or "/",
        parts.query,
        "",
    ))
    return UrlDecision(True, normalized, "allowed", tuple(resolved))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a URL before allowing a GPT/agent backend to fetch it.")
    parser.add_argument("url")
    parser.add_argument("--allow-http", action="store_true")
    parser.add_argument("--resolve-dns", action="store_true", help="Resolve hostnames and reject non-public results")
    args = parser.parse_args()

    result = evaluate_url(args.url, allow_http=args.allow_http, resolve_dns=args.resolve_dns)
    print(json.dumps(asdict(result), indent=2))
    return 0 if result.allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
