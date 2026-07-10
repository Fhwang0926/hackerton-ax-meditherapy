from __future__ import annotations

import json
import re
import os
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def review_with_bundled_mcp(server_path: Path, pending_path: Path, output_path: Path) -> list[dict]:
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    phrases = [str(item["phrase"]) for item in pending]
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "review_cosmetic_claims", "arguments": {"phrases": phrases}},
        },
    ]
    result = subprocess.run(
        [sys.executable, str(server_path)],
        input="\n".join(json.dumps(item, ensure_ascii=False) for item in requests) + "\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    tool_response = next(item for item in responses if item.get("id") == 2)
    findings = tool_response["result"]["structuredContent"]["findings"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")
    return findings


def verify_legal_sources(findings: list[dict], timeout: int = 10) -> list[dict]:
    urls = sorted(
        {
            match.group(0).rstrip(")")
            for finding in findings
            for match in re.finditer(r"https?://[^\s)]+", str(finding.get("citation", "")))
        }
    )
    results = []
    for url in urls:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 MediInsight/0.3 legal-source-verifier"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response.read(1024)
                results.append(
                    {
                        "url": url,
                        "status": "reachable",
                        "http_status": getattr(response, "status", None),
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            curl_status = verify_with_curl(url, timeout) if is_ssl_error(exc) else None
            if curl_status is not None:
                results.append(
                    {
                        "url": url,
                        "status": "reachable" if 200 <= curl_status < 400 else "unreachable",
                        "http_status": curl_status,
                        "transport": "curl_ssl_fallback",
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                continue
            results.append(
                {
                    "url": url,
                    "status": "unreachable",
                    "error": str(exc),
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
            )
    return results


def is_ssl_error(exc: Exception) -> bool:
    return isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, ssl.SSLError)


def verify_with_curl(url: str, timeout: int) -> int | None:
    curl = shutil.which("curl")
    if not curl:
        return None
    try:
        result = subprocess.run(
            [
                curl,
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                str(timeout),
                "--output",
                os.devnull,
                "--write-out",
                "%{http_code}",
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )
        return int(result.stdout.strip())
    except (subprocess.SubprocessError, OSError, ValueError):
        return None
