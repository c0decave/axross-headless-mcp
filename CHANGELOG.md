# Changelog

What changed in each release of axross-headless-mcp. The code is axross's MCP
server (https://github.com/c0decave/axross), written out by axross's
`scripts/export_standalone.py mcp`; its version is axross's.

## 0.15.179 - 2026-11-19

The first public release.

- **axross's MCP server without Qt:** file tools for any MCP client on the
  local disk and, through axross's saved connection profiles, on SFTP, SMB,
  WebDAV, S3, Azure, cloud drives, FTP, NFS and more - over stdio or HTTP
  (bearer token, mTLS).
- **Safe by default:** read-only unless `--mcp-write`, every path confined to
  `--mcp-root`, private keys and tokens refused unless
  `--mcp-allow-secret-reads`; scripts and remote commands are separate
  opt-ins.
- **MCP 2025-11-25, 2025-06-18 and 2024-11-05:** tool annotations, structured
  results with output schemas, progress, cancellation, logging, `axross://`
  resources, background tasks.
- **Hardened** in nine rounds of an adversarial review: bounded answers and
  listings, whole-or-nothing outputs, fair admission of HTTP connections,
  per-backend write locks, secrets found in every encoding.
- **Also as** the container image `ghcr.io/c0decave/axross-headless-mcp` and the
  entry `io.github.c0decave/axross-headless-mcp` in the official MCP Registry
  (both published from axross's release workflow).

Known limitation: over HTTP, from the client's own address (or its IPv6 /64),
connections that trickle a byte every few milliseconds look more alive than a
slow TLS handshake and can push it out of a full server.
