from .docker_tools import ALL_DOCKER_TOOLS
from .system_tools import ALL_SYSTEM_TOOLS


def get_all_tools() -> list:
    return ALL_DOCKER_TOOLS + ALL_SYSTEM_TOOLS
