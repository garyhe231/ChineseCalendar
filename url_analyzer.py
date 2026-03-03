#!/usr/bin/env python3
"""
URL Connection Analyzer

Analyzes the connection details to a given URL, providing timing breakdowns,
diagnostics, and actionable suggestions for connection issues.

Usage:
    python3 url_analyzer.py <url>
    python3 url_analyzer.py https://example.com
    python3 url_analyzer.py -v https://example.com   # verbose mode
"""

import argparse
import http.client
import json
import socket
import ssl
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Status(Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class DNSResult:
    status: Status = Status.OK
    duration_ms: float = 0.0
    resolved_ips: list = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class TCPResult:
    status: Status = Status.OK
    duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class TLSResult:
    status: Status = Status.OK
    duration_ms: float = 0.0
    protocol_version: Optional[str] = None
    cipher: Optional[str] = None
    cert_subject: Optional[str] = None
    cert_issuer: Optional[str] = None
    cert_expiry: Optional[str] = None
    error: Optional[str] = None


@dataclass
class HTTPResult:
    status: Status = Status.OK
    duration_ms: float = 0.0
    status_code: Optional[int] = None
    reason: Optional[str] = None
    headers: dict = field(default_factory=dict)
    redirect_url: Optional[str] = None
    content_length: Optional[int] = None
    server: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AnalysisReport:
    url: str
    hostname: str
    port: int
    is_https: bool
    dns: DNSResult = field(default_factory=DNSResult)
    tcp: TCPResult = field(default_factory=TCPResult)
    tls: Optional[TLSResult] = None
    http: HTTPResult = field(default_factory=HTTPResult)
    total_ms: float = 0.0
    issues: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)


# ── Thresholds ──────────────────────────────────────────────────────────

DNS_SLOW_MS = 200
TCP_SLOW_MS = 500
TLS_SLOW_MS = 500
HTTP_SLOW_MS = 2000
TOTAL_SLOW_MS = 3000
TIMEOUT_SECONDS = 10


# ── Analysis Steps ──────────────────────────────────────────────────────

def resolve_dns(hostname: str) -> DNSResult:
    result = DNSResult()
    start = time.monotonic()
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        result.duration_ms = (time.monotonic() - start) * 1000
        seen = set()
        for family, _, _, _, sockaddr in infos:
            ip = sockaddr[0]
            if ip not in seen:
                seen.add(ip)
                label = "IPv6" if family == socket.AF_INET6 else "IPv4"
                result.resolved_ips.append(f"{ip} ({label})")
        if not result.resolved_ips:
            result.status = Status.ERROR
            result.error = "DNS resolved but returned no addresses"
    except socket.gaierror as e:
        result.duration_ms = (time.monotonic() - start) * 1000
        result.status = Status.ERROR
        result.error = f"DNS resolution failed: {e}"
    return result


def connect_tcp(hostname: str, port: int, ip_hint: Optional[str] = None) -> TCPResult:
    result = TCPResult()
    target = ip_hint or hostname
    start = time.monotonic()
    try:
        sock = socket.create_connection((target, port), timeout=TIMEOUT_SECONDS)
        result.duration_ms = (time.monotonic() - start) * 1000
        sock.close()
    except socket.timeout:
        result.duration_ms = (time.monotonic() - start) * 1000
        result.status = Status.ERROR
        result.error = f"TCP connection timed out after {TIMEOUT_SECONDS}s"
    except OSError as e:
        result.duration_ms = (time.monotonic() - start) * 1000
        result.status = Status.ERROR
        result.error = f"TCP connection failed: {e}"
    return result


def negotiate_tls(hostname: str, port: int) -> TLSResult:
    result = TLSResult()
    ctx = ssl.create_default_context()
    start = time.monotonic()
    try:
        raw = socket.create_connection((hostname, port), timeout=TIMEOUT_SECONDS)
        with ctx.wrap_socket(raw, server_hostname=hostname) as ssock:
            result.duration_ms = (time.monotonic() - start) * 1000
            result.protocol_version = ssock.version()
            cipher_info = ssock.cipher()
            if cipher_info:
                result.cipher = f"{cipher_info[0]} ({cipher_info[1]})"

            cert = ssock.getpeercert()
            if cert:
                subj = dict(x[0] for x in cert.get("subject", []))
                result.cert_subject = subj.get("commonName", "N/A")
                issuer = dict(x[0] for x in cert.get("issuer", []))
                result.cert_issuer = issuer.get("organizationName", "N/A")
                result.cert_expiry = cert.get("notAfter", "N/A")
            ssock.close()
    except ssl.SSLCertVerificationError as e:
        result.duration_ms = (time.monotonic() - start) * 1000
        result.status = Status.ERROR
        result.error = f"Certificate verification failed: {e}"
    except ssl.SSLError as e:
        result.duration_ms = (time.monotonic() - start) * 1000
        result.status = Status.ERROR
        result.error = f"TLS handshake failed: {e}"
    except OSError as e:
        result.duration_ms = (time.monotonic() - start) * 1000
        result.status = Status.ERROR
        result.error = f"Connection error during TLS: {e}"
    return result


def fetch_http(url: str, hostname: str, port: int, is_https: bool) -> HTTPResult:
    result = HTTPResult()
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"

    start = time.monotonic()
    try:
        if is_https:
            conn = http.client.HTTPSConnection(hostname, port, timeout=TIMEOUT_SECONDS)
        else:
            conn = http.client.HTTPConnection(hostname, port, timeout=TIMEOUT_SECONDS)

        conn.request("HEAD", path, headers={
            "User-Agent": "URL-Connection-Analyzer/1.0",
            "Accept": "*/*",
        })
        resp = conn.getresponse()
        result.duration_ms = (time.monotonic() - start) * 1000

        result.status_code = resp.status
        result.reason = resp.reason
        result.headers = dict(resp.getheaders())
        result.server = result.headers.get("Server") or result.headers.get("server")
        cl = result.headers.get("Content-Length") or result.headers.get("content-length")
        if cl:
            try:
                result.content_length = int(cl)
            except ValueError:
                pass

        if resp.status in (301, 302, 303, 307, 308):
            result.redirect_url = result.headers.get("Location") or result.headers.get("location")

        if 400 <= resp.status < 500:
            result.status = Status.WARNING
        elif resp.status >= 500:
            result.status = Status.ERROR

        conn.close()
    except Exception as e:
        result.duration_ms = (time.monotonic() - start) * 1000
        result.status = Status.ERROR
        result.error = f"HTTP request failed: {e}"
    return result


# ── Diagnostics ─────────────────────────────────────────────────────────

def diagnose(report: AnalysisReport) -> None:
    """Populate issues and suggestions based on the collected results."""
    # DNS checks
    if report.dns.status == Status.ERROR:
        report.issues.append(f"DNS resolution failed: {report.dns.error}")
        report.suggestions.append(
            "Check that the hostname is spelled correctly. "
            "Try 'nslookup {host}' or 'dig {host}' to verify DNS.".format(host=report.hostname)
        )
        return  # nothing else to check
    if report.dns.duration_ms > DNS_SLOW_MS:
        report.issues.append(f"DNS resolution is slow ({report.dns.duration_ms:.0f} ms)")
        report.suggestions.append(
            "Consider switching to a faster DNS resolver (e.g. 1.1.1.1 or 8.8.8.8). "
            "Your local DNS cache may also be cold."
        )

    # TCP checks
    if report.tcp.status == Status.ERROR:
        report.issues.append(f"TCP connection failed: {report.tcp.error}")
        if "timed out" in (report.tcp.error or ""):
            report.suggestions.append(
                "The server is not responding on port {p}. "
                "A firewall may be blocking the connection, or the server may be down.".format(p=report.port)
            )
        else:
            report.suggestions.append(
                "Check that the server is running and port {p} is open. "
                "Try 'telnet {h} {p}' to test connectivity.".format(h=report.hostname, p=report.port)
            )
        return
    if report.tcp.duration_ms > TCP_SLOW_MS:
        report.issues.append(f"TCP handshake is slow ({report.tcp.duration_ms:.0f} ms)")
        report.suggestions.append(
            "High TCP latency usually indicates network distance or congestion. "
            "Consider a CDN or a server closer to you."
        )

    # TLS checks
    if report.tls:
        if report.tls.status == Status.ERROR:
            report.issues.append(f"TLS error: {report.tls.error}")
            if "verification" in (report.tls.error or "").lower():
                report.suggestions.append(
                    "The server's SSL certificate is invalid or untrusted. "
                    "Check cert expiry, CN/SAN mismatch, or missing intermediates."
                )
            else:
                report.suggestions.append(
                    "TLS handshake failed. The server may not support modern TLS versions."
                )
        elif report.tls.duration_ms > TLS_SLOW_MS:
            report.issues.append(f"TLS handshake is slow ({report.tls.duration_ms:.0f} ms)")
            report.suggestions.append(
                "Slow TLS can be caused by certificate chain length, OCSP stapling issues, "
                "or the server being under load."
            )

    # HTTP checks
    if report.http.status == Status.ERROR:
        report.issues.append(f"HTTP request failed: {report.http.error}")
        report.suggestions.append(
            "The server accepted the connection but the HTTP request failed. "
            "Check if the URL path is correct."
        )
    elif report.http.status_code:
        if report.http.status_code >= 500:
            report.issues.append(f"Server returned HTTP {report.http.status_code} ({report.http.reason})")
            report.suggestions.append("The server is experiencing an internal error. Try again later.")
        elif report.http.status_code == 403:
            report.issues.append("Access forbidden (HTTP 403)")
            report.suggestions.append(
                "The server is blocking this request. "
                "You may need authentication or the resource may be restricted."
            )
        elif report.http.status_code == 404:
            report.issues.append("Resource not found (HTTP 404)")
            report.suggestions.append("The URL path may be incorrect. Double-check the path.")
        elif report.http.status_code in (301, 302, 303, 307, 308):
            target = report.http.redirect_url or "unknown"
            report.issues.append(f"Redirect to: {target}")
            report.suggestions.append(
                "The URL redirects to another location. Use the target URL directly for faster access."
            )

    if report.http.duration_ms > HTTP_SLOW_MS:
        report.issues.append(f"HTTP response is slow ({report.http.duration_ms:.0f} ms)")
        report.suggestions.append(
            "Slow HTTP response can mean the server is under heavy load, "
            "the backend is slow, or the response is very large."
        )

    # Overall
    if report.total_ms > TOTAL_SLOW_MS and not report.issues:
        report.issues.append(f"Total connection time is high ({report.total_ms:.0f} ms)")
        report.suggestions.append(
            "Overall latency is above {t}ms. Consider a CDN, caching, or a geographically "
            "closer server.".format(t=TOTAL_SLOW_MS)
        )

    if not report.issues:
        report.issues.append("No issues detected — connection looks healthy!")


# ── Display ─────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
DIM = "\033[2m"

BAR_WIDTH = 40


def _status_icon(status: Status) -> str:
    return {Status.OK: f"{GREEN}✓{RESET}", Status.WARNING: f"{YELLOW}!{RESET}", Status.ERROR: f"{RED}✗{RESET}"}[status]


def _bar(ms: float, total: float) -> str:
    if total == 0:
        return ""
    frac = min(ms / total, 1.0)
    filled = int(frac * BAR_WIDTH)
    return f"{CYAN}{'█' * filled}{'░' * (BAR_WIDTH - filled)}{RESET}"


def print_report(report: AnalysisReport, verbose: bool = False) -> None:
    print()
    print(f"{BOLD}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║           URL Connection Analysis Report                    ║{RESET}")
    print(f"{BOLD}╚══════════════════════════════════════════════════════════════╝{RESET}")
    print()
    print(f"  {BOLD}URL:{RESET}    {report.url}")
    print(f"  {BOLD}Host:{RESET}   {report.hostname}:{report.port}")
    print(f"  {BOLD}Scheme:{RESET} {'HTTPS' if report.is_https else 'HTTP'}")
    print()

    # ── Timing breakdown ────────────────────────────────────────────
    print(f"{BOLD}  ── Timing Breakdown ─────────────────────────────────────────{RESET}")
    print()

    total = report.total_ms or 1

    # DNS
    s = _status_icon(report.dns.status)
    print(f"  {s} DNS Resolution     {report.dns.duration_ms:>8.1f} ms  {_bar(report.dns.duration_ms, total)}")
    if verbose and report.dns.resolved_ips:
        for ip in report.dns.resolved_ips:
            print(f"    {DIM}→ {ip}{RESET}")

    # TCP
    s = _status_icon(report.tcp.status)
    print(f"  {s} TCP Handshake      {report.tcp.duration_ms:>8.1f} ms  {_bar(report.tcp.duration_ms, total)}")

    # TLS
    if report.tls:
        s = _status_icon(report.tls.status)
        print(f"  {s} TLS Handshake      {report.tls.duration_ms:>8.1f} ms  {_bar(report.tls.duration_ms, total)}")
        if verbose and report.tls.status == Status.OK:
            print(f"    {DIM}→ Protocol: {report.tls.protocol_version}{RESET}")
            print(f"    {DIM}→ Cipher:   {report.tls.cipher}{RESET}")
            print(f"    {DIM}→ Subject:  {report.tls.cert_subject}{RESET}")
            print(f"    {DIM}→ Issuer:   {report.tls.cert_issuer}{RESET}")
            print(f"    {DIM}→ Expires:  {report.tls.cert_expiry}{RESET}")

    # HTTP
    s = _status_icon(report.http.status)
    status_str = ""
    if report.http.status_code:
        status_str = f"  [HTTP {report.http.status_code} {report.http.reason}]"
    print(f"  {s} HTTP Response      {report.http.duration_ms:>8.1f} ms  {_bar(report.http.duration_ms, total)}{status_str}")
    if verbose and report.http.server:
        print(f"    {DIM}→ Server: {report.http.server}{RESET}")
    if verbose and report.http.content_length is not None:
        print(f"    {DIM}→ Content-Length: {report.http.content_length}{RESET}")

    print(f"  {'─' * 60}")
    print(f"  {BOLD}  Total              {report.total_ms:>8.1f} ms{RESET}")
    print()

    # ── Diagnosis ───────────────────────────────────────────────────
    print(f"{BOLD}  ── Diagnosis ────────────────────────────────────────────────{RESET}")
    print()
    for issue in report.issues:
        if "No issues" in issue:
            print(f"  {GREEN}● {issue}{RESET}")
        else:
            print(f"  {YELLOW}● {issue}{RESET}")
    print()

    if report.suggestions and not any("No issues" in i for i in report.issues):
        print(f"{BOLD}  ── Suggestions ──────────────────────────────────────────────{RESET}")
        print()
        for suggestion in report.suggestions:
            print(f"  {CYAN}→ {suggestion}{RESET}")
        print()

    # ── Verdict ─────────────────────────────────────────────────────
    errors = sum(1 for r in [report.dns, report.tcp, report.tls, report.http] if r and r.status == Status.ERROR)
    warnings = sum(1 for r in [report.dns, report.tcp, report.tls, report.http] if r and r.status == Status.WARNING)

    if errors:
        verdict = f"{RED}{BOLD}CONNECTION FAILED — {errors} error(s) detected{RESET}"
    elif warnings or report.total_ms > TOTAL_SLOW_MS:
        verdict = f"{YELLOW}{BOLD}CONNECTION OK — but with {warnings} warning(s) / slow performance{RESET}"
    else:
        verdict = f"{GREEN}{BOLD}CONNECTION HEALTHY — everything looks good!{RESET}"
    print(f"  {verdict}")
    print()


# ── JSON output ─────────────────────────────────────────────────────────

def report_to_dict(report: AnalysisReport) -> dict:
    d = {
        "url": report.url,
        "hostname": report.hostname,
        "port": report.port,
        "is_https": report.is_https,
        "total_ms": round(report.total_ms, 1),
        "dns": {
            "status": report.dns.status.value,
            "duration_ms": round(report.dns.duration_ms, 1),
            "resolved_ips": report.dns.resolved_ips,
            "error": report.dns.error,
        },
        "tcp": {
            "status": report.tcp.status.value,
            "duration_ms": round(report.tcp.duration_ms, 1),
            "error": report.tcp.error,
        },
        "http": {
            "status": report.http.status.value,
            "duration_ms": round(report.http.duration_ms, 1),
            "status_code": report.http.status_code,
            "reason": report.http.reason,
            "server": report.http.server,
            "error": report.http.error,
        },
        "issues": report.issues,
        "suggestions": report.suggestions,
    }
    if report.tls:
        d["tls"] = {
            "status": report.tls.status.value,
            "duration_ms": round(report.tls.duration_ms, 1),
            "protocol_version": report.tls.protocol_version,
            "cipher": report.tls.cipher,
            "cert_subject": report.tls.cert_subject,
            "cert_issuer": report.tls.cert_issuer,
            "cert_expiry": report.tls.cert_expiry,
            "error": report.tls.error,
        }
    return d


# ── Main ────────────────────────────────────────────────────────────────

def normalize_url(raw: str) -> str:
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def analyze(url: str) -> AnalysisReport:
    parsed = urllib.parse.urlparse(url)
    is_https = parsed.scheme == "https"
    hostname = parsed.hostname or ""
    default_port = 443 if is_https else 80
    port = parsed.port or default_port

    report = AnalysisReport(url=url, hostname=hostname, port=port, is_https=is_https)

    overall_start = time.monotonic()

    # 1) DNS
    report.dns = resolve_dns(hostname)
    if report.dns.status == Status.ERROR:
        report.total_ms = (time.monotonic() - overall_start) * 1000
        diagnose(report)
        return report

    # 2) TCP
    report.tcp = connect_tcp(hostname, port)
    if report.tcp.status == Status.ERROR:
        report.total_ms = (time.monotonic() - overall_start) * 1000
        diagnose(report)
        return report

    # 3) TLS (only for HTTPS)
    if is_https:
        report.tls = negotiate_tls(hostname, port)

    # 4) HTTP
    report.http = fetch_http(url, hostname, port, is_https)

    report.total_ms = (time.monotonic() - overall_start) * 1000
    diagnose(report)
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Analyze connection details to a URL (DNS, TCP, TLS, HTTP)."
    )
    parser.add_argument("url", help="The URL to analyze (e.g. https://example.com)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show extra details (IPs, certs, ciphers)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    url = normalize_url(args.url)

    if not args.json:
        print(f"\n  {BOLD}Analyzing {url} ...{RESET}\n")

    report = analyze(url)

    if args.json:
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        print_report(report, verbose=args.verbose)


if __name__ == "__main__":
    main()
