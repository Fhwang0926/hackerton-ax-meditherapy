#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mediinsight.compliance import RULES, review_phrases


TOOLS = [
    {
        "name": "review_cosmetic_claims",
        "description": "화장품 광고 문구를 공식 출처가 연결된 로컬 규칙으로 예비 검수합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phrases": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["phrases"],
        },
    },
    {
        "name": "search_cosmetic_ad_law",
        "description": "화장품 표시·광고 검수에 사용한 공식 법령 및 식약처 자료를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]


def response(request_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error:
        payload["error"] = error
    else:
        payload["result"] = result
    return payload


def handle(message: dict) -> dict | None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        return response(
            request_id,
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mediinsight-law", "version": "0.1.0"},
            },
        )
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None
    if method == "tools/list":
        return response(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name == "review_cosmetic_claims":
            findings = [asdict(item) for item in review_phrases(arguments.get("phrases", []), "mediinsight-law")]
            return tool_result(request_id, {"findings": findings, "legal_advice": False})
        if name == "search_cosmetic_ad_law":
            query = str(arguments.get("query", ""))
            sources = sorted(
                {
                    rule["citation"]
                    for rule in RULES
                    if rule.get("citation")
                    and (not query or any(token in str(rule) for token in query.split()))
                }
            )
            if not sources:
                sources = sorted({rule["citation"] for rule in RULES if rule.get("citation")})
            return tool_result(request_id, {"query": query, "sources": sources})
        return response(request_id, error={"code": -32601, "message": f"Unknown tool: {name}"})
    if request_id is not None:
        return response(request_id, error={"code": -32601, "message": f"Unknown method: {method}"})
    return None


def tool_result(request_id, data: dict) -> dict:
    return response(
        request_id,
        {
            "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
            "structuredContent": data,
            "isError": False,
        },
    )


def main() -> None:
    for line in sys.stdin:
        try:
            message = json.loads(line)
            result = handle(message)
            if result is not None:
                print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(
                json.dumps(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(exc)}},
                    ensure_ascii=False,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
