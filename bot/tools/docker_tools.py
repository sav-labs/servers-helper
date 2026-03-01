"""Docker management tools — operate on remote servers via SSH + docker CLI."""

from typing import Annotated

from langchain_core.tools import tool

from .base import ssh_exec


@tool
async def docker_list_containers(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
) -> str:
    """List all Docker containers on the server with their name, image, status and ports."""
    return await ssh_exec(
        server,
        r"docker ps -a --format '{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}'",
    )


@tool
async def docker_container_logs(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    container: Annotated[str, "Container name or ID"],
    lines: Annotated[int, "Number of last log lines to fetch (default 50)"] = 50,
) -> str:
    """Fetch the last N log lines from a Docker container."""
    return await ssh_exec(server, f"docker logs --tail {lines} {container} 2>&1")


@tool
async def docker_container_stats(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
) -> str:
    """Show CPU, memory and network stats for all running containers (single snapshot)."""
    return await ssh_exec(
        server,
        "docker stats --no-stream --format "
        r'"table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"',
    )


@tool
async def docker_inspect_container(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    container: Annotated[str, "Container name or ID"],
) -> str:
    """Inspect a Docker container: image, mounts, env vars, restart policy, health."""
    return await ssh_exec(
        server,
        f"docker inspect {container} --format "
        r'"Image: {{.Config.Image}}\nStatus: {{.State.Status}}\n"'
        r'"RestartPolicy: {{.HostConfig.RestartPolicy.Name}}\n"'
        r'"StartedAt: {{.State.StartedAt}}\nFinishedAt: {{.State.FinishedAt}}"',
    )


@tool
async def docker_restart_container(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    container: Annotated[str, "Container name or ID"],
) -> str:
    """Restart a Docker container. ALWAYS ask user for confirmation before calling this."""
    return await ssh_exec(server, f"docker restart {container}")


@tool
async def docker_stop_container(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    container: Annotated[str, "Container name or ID"],
) -> str:
    """Stop a running Docker container. ALWAYS ask user for confirmation before calling this."""
    return await ssh_exec(server, f"docker stop {container}")


@tool
async def docker_start_container(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    container: Annotated[str, "Container name or ID"],
) -> str:
    """Start a stopped Docker container."""
    return await ssh_exec(server, f"docker start {container}")


@tool
async def docker_exec_command(
    server: Annotated[str, "Server name: vdsina-netherlands | aeza-germany | servers-helper"],
    container: Annotated[str, "Container name or ID"],
    command: Annotated[str, "Shell command to run inside the container"],
) -> str:
    """Execute a command inside a running Docker container. Ask for confirmation for write ops."""
    return await ssh_exec(server, f"docker exec {container} {command}")


ALL_DOCKER_TOOLS = [
    docker_list_containers,
    docker_container_logs,
    docker_container_stats,
    docker_inspect_container,
    docker_restart_container,
    docker_stop_container,
    docker_start_container,
    docker_exec_command,
]
