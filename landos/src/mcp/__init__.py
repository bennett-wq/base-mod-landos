"""LandOS MCP (Model Context Protocol) server and tools.

Exposes the LandOS event mesh as MCP tools for autonomous agent access.
The MCP server runs as a subprocess communicating via stdin/stdout JSON-RPC,
following the pattern from Anthropic's Claude Agent SDK cookbooks.

Architecture:
    Claude Agent SDK  ←→  query() loop streams responses
         │
         ▼
    MCP Server (subprocess via stdio/JSON-RPC)
         │
         ├── Spark tools     (listing ingestion, BBO signals)
         ├── Regrid tools    (parcel ingestion, scoring, linkage)
         ├── Cluster tools   (detection, store queries)
         ├── Trigger tools   (engine evaluation, rule introspection)
         └── Store tools     (listing/parcel/cluster state queries)

Human-in-the-loop:
    Investigation (read-only) and remediation (write) are separate
    agent invocations with human review in between.
"""
