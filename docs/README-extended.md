# axross-headless-mcp: the extended README

Everything on one page; the short version, with the screenshots, is the [README](../README.md) - installing, the tests and the licence are there.

axross's headless MCP server: file tools on the local disk and on SFTP, SMB, WebDAV, S3 and more for any MCP client, over stdio or HTTP - without Qt.

The MCP (Model Context Protocol) server of [axross](https://github.com/c0decave/axross)
on its own: an LLM client - Claude Desktop, Claude Code, Cursor, VS Code, any MCP client -
lists, reads, searches and hashes files on this machine and on axross's remote
connections, and with `--mcp-write` writes them. No GUI and no Qt: it runs on a server,
in a container or in CI.

- **File tools** (always on, read-only): `list_dir`, `stat`, `read_file`, `checksum`,
  `search`, `walk`, `recursive_checksum`, `grep`, `list_versions`, `open_version_read`,
  and `preview` (image thumbnails; with the `images` extra, which brings Pillow).
- **Write tools** (`--mcp-write --mcp-root DIR`): `write_file`, `mkdir`, `remove`,
  `rename`, `copy`, `bulk_copy`, `symlink`, `hardlink`, `chmod`.
- **Capability groups** (`--mcp-tools GROUP,...` or `all`): metadata, duplicates,
  packer, archive, crypto, index, filetype, transfer, remote (axross's saved
  connection profiles as further backends), exec (`--mcp-allow-exec`), agent,
  extensions.
- Every path is confined to `--mcp-root` (default: your home folder); secret files
  (SSH and GnuPG private keys, tokens) are refused unless `--mcp-allow-secret-reads`.

The protocol: MCP 2025-11-25, 2025-06-18 and 2024-11-05 (the client's version is
answered when it is one of them), tool annotations (read-only, destructive,
idempotent, open-world), structured results with output schemas, progress,
cancellation, logging and `axross://` resources. Long jobs run in the background
through axross's own `axross/tasks/start` / `status` / `cancel` / `list`. A file
name that is not UTF-8 is shown with U+FFFD and comes with its raw bytes
(`name_b64`, `path_b64`); every path argument takes them back (`path_b64`, ...).
The audit trail (what each tool did or refused) goes to stderr and to the log.

### Install

```sh
pipx install axross-headless-mcp                  # or: pip install axross-headless-mcp
pipx install 'axross-headless-mcp[all]'           # with every remote protocol and format
axross-headless-mcp --version
axross-headless-mcp --mcp-list-tools --mcp-tools all   # what it would serve, as JSON
```

The extras are axross's: `smb`, `webdav`, `s3`, `azure`, `onedrive`, `gdrive`,
`dropbox`, `winrm`, `wmi`, `exchange`, `adb`, `archive`, `tftp`, `postgres`, `redis`,
`mongo`, `git`, `dns`, `magic`, `encoding`, `snmp`, `ldap`, `metadata`, plus `images`
(Pillow); `all` holds what axross's own `all` holds (not `winrm`, `wmi`, `exchange`)
plus `images`. SFTP / SSH (paramiko) is always there.

### Connect a client (stdio)

Claude Code:

```sh
claude mcp add axross -- axross-headless-mcp --mcp-root ~/projects --mcp-tools all
```

Claude Desktop, Cursor, VS Code and the like (`claude_desktop_config.json`,
`.cursor/mcp.json`, ...):

```json
{
  "mcpServers": {
    "axross": {
      "command": "axross-headless-mcp",
      "args": ["--mcp-root", "/home/me/projects", "--mcp-tools", "all"]
    }
  }
}
```

Add `--mcp-write` for the write tools (it needs an explicit `--mcp-root`).
`uvx axross-headless-mcp ...` works as the command as well, without installing first.

### Over HTTP

```sh
axross-headless-mcp --mcp-http 127.0.0.1:7331 --mcp-root ~/projects --mcp-tools all
# prints a bearer token (or set AXROSS_MCP_HTTP_TOKEN); the endpoint is
# http://127.0.0.1:7331/messages (streamable HTTP, Mcp-Session-Id, SSE)
```

A client sends `Authorization: Bearer <token>`. Anything but loopback needs mTLS:
`--mcp-cert server.pem --mcp-key server-key.pem --mcp-ca clients-ca.pem`.
`--mcp-allow-scripts` and `--mcp-allow-secret-reads` are stdio-only.

### Docker

```sh
docker run -i --rm -v "$PWD:/data" ghcr.io/c0decave/axross-headless-mcp:latest     --mcp-server --mcp-root /data --mcp-tools all
```

### Settings

The server reads axross's settings (`~/.config/axross`): the saved connection
profiles of the `remote` group (credentials from the system keyring), the metadata
and duplicate indexes, the security mode. The log goes to
`~/.local/state/axross/logs/axross.log` (`--debug` / `-v`: also stderr; stdout is the
protocol's).

Full reference: [docs/MCP.md](https://github.com/c0decave/axross/blob/main/docs/MCP.md)
and the tool catalogue [docs/mcp-tools.json](https://github.com/c0decave/axross/blob/main/docs/mcp-tools.json).
Setup steps for AI agents (Cline and others):
[llms-install.md](https://github.com/c0decave/axross-headless-mcp/blob/main/llms-install.md).

## Where it comes from

It is the same code as in [axross](https://github.com/c0decave/axross), written out by
axross's `scripts/export_standalone.py mcp`; it reads axross's settings
(`~/.config/axross`) and axross's saved connection profiles.

