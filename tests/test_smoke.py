"""axross-headless-mcp answers an MCP client over stdio and over HTTP - every tool
group listed (all,adb: every group), a file read - and PyQt6 is never imported. The installed
package when there is one, else this checkout's src/."""

import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
#: Runs the command in this interpreter and says on stderr whether Qt came in.
PROBE = ("import atexit, sys; atexit.register(lambda: sys.stderr.write("
         "'QT=%s\\n' % any(m.split('.')[0] == 'PyQt6' for m in sys.modules))); "
         "from axross_headless_mcp.__main__ import main; sys.exit(main())")
GROUP_TOOLS = {"read_metadata", "list_duplicate_groups", "list_archive_formats",
               "list_archive_members", "build_index", "identify_file_type",
               "list_remote_profiles", "run_llm_agent", "list_extensions", "get_device_info"}
#: Served only with --mcp-write.
WRITE_TOOLS = {"write_file", "copy_path_to_backend", "create_archive", "extract_archive",
               "encrypt_file", "install_app"}


def _env(home: Path, **extra) -> dict:
    env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
               XDG_DATA_HOME=str(home / ".local" / "share"), XDG_STATE_HOME=str(home / ".state"),
               XDG_CACHE_HOME=str(home / ".cache"),
               PYTHON_KEYRING_BACKEND="keyring.backends.null.Keyring", **extra)
    if importlib.util.find_spec("axross_headless_mcp") is None:  # not installed: this checkout
        env["PYTHONPATH"] = os.pathsep.join(p for p in (str(ROOT / "src"),
                                                        os.environ.get("PYTHONPATH", "")) if p)
    for name in ("DISPLAY", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM", "AXROSS_MCP_TOOLS"):
        env.pop(name, None)
    return env


def _data(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    (data / "hello.txt").write_text("hello from axross-headless-mcp\n", encoding="utf-8")
    return data


def test_happy_stdio_initialize_lists_every_group_and_reads_a_file(tmp_path):
    data = _data(tmp_path)
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-11-25", "capabilities": {},
                    "clientInfo": {"name": "smoke", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "read_file",
                    "arguments": {"path": str(data / "hello.txt"), "encoding": "text"}}},
    ]
    proc = subprocess.run(
        [sys.executable, "-c", PROBE, "--mcp-root", str(data), "--mcp-tools", "all,adb",
         "--mcp-write"],
        input="".join(json.dumps(r) + "\n" for r in requests), capture_output=True,
        text=True, timeout=120, env=_env(tmp_path), cwd=tmp_path)
    replies = {m.get("id"): m for m in map(json.loads, proc.stdout.splitlines())}
    assert replies[1]["result"]["protocolVersion"] == "2025-11-25", proc.stderr[-2000:]
    names = {t["name"] for t in replies[2]["result"]["tools"]}
    assert GROUP_TOOLS | WRITE_TOOLS <= names, (GROUP_TOOLS | WRITE_TOOLS) - names
    result = replies[3]["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["text"] == "hello from axross-headless-mcp\n"
    assert "QT=False" in proc.stderr


def test_happy_the_manifest_of_every_group(tmp_path):
    proc = subprocess.run([sys.executable, "-c", PROBE, "--mcp-list-tools", "--mcp-tools", "all,adb"],
                          capture_output=True, text=True, timeout=120, env=_env(tmp_path),
                          cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr[-2000:]
    manifest = json.loads(proc.stdout)
    assert GROUP_TOOLS <= {t["name"] for t in manifest["tools"]}
    assert "QT=False" in proc.stderr


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _post(url, body, token, session=None, version=None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}",
               "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    if version:
        headers["MCP-Protocol-Version"] = version
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, dict(response.headers), json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), None


def test_happy_http_initialize_lists_every_group_and_reads_a_file(tmp_path):
    data = _data(tmp_path)
    port, token = _free_port(), "smoke-token-0123456789"
    proc = subprocess.Popen(
        [sys.executable, "-c", PROBE, "--mcp-http", f"127.0.0.1:{port}", "--mcp-root", str(data),
         "--mcp-tools", "all,adb"], env=_env(tmp_path, AXROSS_MCP_HTTP_TOKEN=token), cwd=tmp_path,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    url = f"http://127.0.0.1:{port}/messages"
    try:
        deadline = time.time() + 60
        while True:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2).read()
                break
            except OSError:
                assert proc.poll() is None and time.time() < deadline, "the server did not start"
                time.sleep(0.2)
        status, headers, init = _post(url, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "smoke", "version": "0"}}}, token)
        assert status == 200 and init["result"]["protocolVersion"] == "2025-06-18"
        session = {k.lower(): v for k, v in headers.items()}["mcp-session-id"]
        status, _h, _b = _post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"},
                               token, session, "2025-06-18")
        assert status == 202
        status, _h, listing = _post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                                    token, session, "2025-06-18")
        assert GROUP_TOOLS <= {t["name"] for t in listing["result"]["tools"]}
        status, _h, read = _post(url, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "read_file",
                       "arguments": {"path": str(data / "hello.txt"), "encoding": "text"}}},
            token, session, "2025-06-18")
        assert read["result"]["structuredContent"]["text"] == "hello from axross-headless-mcp\n"
        status, _h, _b = _post(url, {"jsonrpc": "2.0", "id": 4, "method": "ping"},
                               token, session, "1999-01-01")
        assert status == 400  # a protocol version the server does not speak
    finally:
        proc.terminate()
        try:
            _out, err = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            _out, err = proc.communicate()
    assert "QT=True" not in err
