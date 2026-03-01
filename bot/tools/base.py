"""SSH execution helper used by all tools."""

import asyncio

from config import app_config


async def ssh_exec(server: str, command: str, timeout: int = 30) -> str:
    """Execute a shell command on the given server via SSH.

    Uses the system SSH client and ~/.ssh/config on the host, so host aliases,
    keys and jump-hosts defined there are resolved automatically.
    """
    if server not in app_config.servers:
        available = ", ".join(app_config.servers)
        return f"[error] Unknown server '{server}'. Available: {available}"

    ssh_host = app_config.servers[server].ssh_host

    proc = await asyncio.create_subprocess_exec(
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        "-o", "BatchMode=yes",
        ssh_host,
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return f"[error] Command timed out after {timeout}s"

    out = stdout.decode("utf-8", errors="replace").strip()
    err = stderr.decode("utf-8", errors="replace").strip()

    if proc.returncode != 0 and err:
        return f"{out}\n[stderr] {err}".strip() if out else f"[stderr] {err}"

    return out or "(empty output)"
