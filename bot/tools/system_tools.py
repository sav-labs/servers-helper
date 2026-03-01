"""System-level tools: resources, services, shell commands."""

from typing import Annotated

from langchain_core.tools import tool

from .base import ssh_exec


@tool
async def system_resources(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
) -> str:
    """Get CPU load, RAM usage, disk usage and uptime for the server."""
    command = (
        "echo '=== Uptime ===' && uptime && "
        "echo '=== Memory ===' && free -h && "
        "echo '=== Disk ===' && df -h --output=source,size,used,avail,pcent,target "
        "| grep -v tmpfs | grep -v udev"
    )
    return await ssh_exec(server, command)


@tool
async def system_processes(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    count: Annotated[int, "Number of top processes to show (default 10)"] = 10,
) -> str:
    """Show top processes by CPU usage on the server."""
    return await ssh_exec(
        server,
        f"ps aux --sort=-%cpu | head -n {count + 1}",
    )


@tool
async def system_service_status(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    service: Annotated[str, "Systemd service name, e.g. 'nginx' or 'docker'"],
) -> str:
    """Check the status of a systemd service on the server."""
    return await ssh_exec(server, f"systemctl status {service} --no-pager -l")


@tool
async def system_network_info(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
) -> str:
    """Show network interfaces, IP addresses and open listening ports."""
    command = (
        "echo '=== Interfaces ===' && ip -brief addr && "
        "echo '=== Listening ports ===' && ss -tlnp"
    )
    return await ssh_exec(server, command)


@tool
async def system_run_command(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    command: Annotated[str, "Shell command to execute on the server"],
) -> str:
    """Run an arbitrary shell command on the server.

    Use for read-only diagnostics (logs, configs, status checks).
    For commands that make changes, ALWAYS ask user for confirmation first.
    """
    return await ssh_exec(server, command)


@tool
async def system_journal_logs(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    unit: Annotated[str, "Systemd unit name, or empty string for system journal"] = "",
    lines: Annotated[int, "Number of last log lines (default 50)"] = 50,
) -> str:
    """Read systemd journal logs for a service or the whole system."""
    unit_flag = f"-u {unit}" if unit else ""
    return await ssh_exec(server, f"journalctl {unit_flag} -n {lines} --no-pager")


ALL_SYSTEM_TOOLS = [
    system_resources,
    system_processes,
    system_service_status,
    system_network_info,
    system_run_command,
    system_journal_logs,
]
