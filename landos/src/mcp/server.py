"""LandOS MCP Server — JSON-RPC over stdio.

Runs as a subprocess spawned by Claude Agent SDK. Communicates via
stdin/stdout using the MCP JSON-RPC protocol.

Usage:
    python -m src.mcp.server

Architecture follows the SRE cookbook pattern:
    Claude Agent SDK → spawns this process → tools/list → tools/call
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from src.mcp.handlers import MeshState, dispatch_tool
from src.mcp.tools import ALL_TOOLS, MUTATION_TOOL_NAMES


# Global mesh state — initialized once, shared across all tool calls
_mesh: MeshState | None = None


def _get_mesh() -> MeshState:
    """Lazy-init the global MeshState."""
    global _mesh
    if _mesh is None:
        _mesh = MeshState()
    return _mesh


async def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle a single JSON-RPC request from the Claude Agent SDK."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "landos-mesh",
                    "version": "0.1.0",
                },
            },
        }

    if method == "notifications/initialized":
        # Acknowledgment — no response needed
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": ALL_TOOLS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        mesh = _get_mesh()
        result = await dispatch_tool(mesh, tool_name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}",
        },
    }


async def main() -> None:
    """Main event loop: read JSON-RPC from stdin, respond on stdout."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    # Use stdout in binary mode for writing
    writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.Protocol, sys.stdout
    )

    buffer = b""
    while True:
        chunk = await reader.read(4096)
        if not chunk:
            break
        buffer += chunk

        # Process complete lines (each JSON-RPC message is one line)
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            response = await handle_request(request)
            if response is not None:
                response_bytes = json.dumps(response).encode("utf-8") + b"\n"
                writer_transport.write(response_bytes)


if __name__ == "__main__":
    asyncio.run(main())
