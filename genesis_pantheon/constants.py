"""Constants for the GenesisPantheon framework."""

from pathlib import Path

# Package root
PANTHEON_ROOT: Path = Path(__file__).parent

# Default paths
DEFAULT_WORKSPACE_ROOT: Path = Path.home() / ".genesis_pantheon" / "workspace"
DEFAULT_CONFIG_DIR: Path = Path.home() / ".genesis_pantheon"
DEFAULT_CONFIG_FILE: Path = Path.home() / ".genesis_pantheon" / "blueprint.yaml"

# Signal routing constants
SIGNAL_ROUTE_TO_ALL: str = "<all>"
SIGNAL_ROUTE_TO_SELF: str = "<self>"
SIGNAL_ROUTE_FROM: str = "sent_from"
SIGNAL_ROUTE_TO: str = "send_to"
SIGNAL_ROUTE_CAUSE_BY: str = "cause_by"

# Agent identifier
AGENT: str = "agent"

# Serialization path
SERDESER_PATH: Path = DEFAULT_WORKSPACE_ROOT / "storage"

# File repository directory names
DOCS_FILE_REPO: str = "docs"
RESOURCES_FILE_REPO: str = "resources"
SRC_FILE_REPO: str = "src"
TESTS_FILE_REPO: str = "tests"

# Document types
PRD_FILENAME: str = "prd.md"
SYSTEM_DESIGN_FILENAME: str = "system_design.md"
TASK_FILENAME: str = "tasks.md"
CODE_FILENAME: str = "code.py"

# System prompts
SYSTEM_PROMPT_TEMPLATE: str = (
    "You are a {profile}, named {name}. "
    "Your goal is {goal}. "
    "Constraints: {constraints}"
)

__all__ = [
    "PANTHEON_ROOT",
    "DEFAULT_WORKSPACE_ROOT",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_CONFIG_FILE",
    "SIGNAL_ROUTE_TO_ALL",
    "SIGNAL_ROUTE_TO_SELF",
    "SIGNAL_ROUTE_FROM",
    "SIGNAL_ROUTE_TO",
    "SIGNAL_ROUTE_CAUSE_BY",
    "AGENT",
    "SERDESER_PATH",
    "DOCS_FILE_REPO",
    "RESOURCES_FILE_REPO",
    "SRC_FILE_REPO",
    "TESTS_FILE_REPO",
    "PRD_FILENAME",
    "SYSTEM_DESIGN_FILENAME",
    "TASK_FILENAME",
    "CODE_FILENAME",
    "SYSTEM_PROMPT_TEMPLATE",
]
