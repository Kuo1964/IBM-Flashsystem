# 0002 FastMCP and MCPServer Dual Fallback Import

## Context and Decision

The Model Context Protocol (`mcp`) SDK 2.0 refactored internal module exports, replacing legacy `from mcp.server.fastmcp import FastMCP` imports with `from mcp.server.mcpserver import MCPServer`. To prevent MCP Server crashes when AI Agents (Antigravity, Claude Desktop) initialize tools across different SDK versions, we implemented a dynamic fallback wrapper using `try...except ModuleNotFoundError` in `mcp_server.py`.

## Status

Accepted
