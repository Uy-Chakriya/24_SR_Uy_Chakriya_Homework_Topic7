from pydantic import ValidationError
from schemas import TOOL_SCHEMAS
from tools import TOOL_FUNCTIONS


MAX_TOOL_CALLS = 6

PERMISSIONS: dict[str, set[str]] = {
    "member": {"search_book", "check_availability", "borrow_book"},
    "librarian": {
        "search_book",
        "check_availability",
        "borrow_book",
        "remove_book"
    },
}

class PermissionDenied(Exception):
    """Raised when a role tries to call a tool it is not allowed to use."""


def check_permission(role: str, tool_name: str) -> None:
    if role not in PERMISSIONS:
        raise PermissionDenied(f"Unknown role '{role}'.")
    if tool_name not in PERMISSIONS[role]:
        raise PermissionDenied(
            f"Role '{role}' is not allowed to call '{tool_name}'."
        )


def safe_call(role: str, tool_name: str, raw_arguments: dict) -> dict:
    if tool_name not in TOOL_FUNCTIONS:
        return {
            "error": "UNKNOWN_TOOL",
            "message": f"Tool '{tool_name}' does not exist."
        }

    try:
        check_permission(role, tool_name)
    except PermissionDenied as e:
        return {
            "error": "PERMISSION_DENIED",
            "message": str(e)
        }

    schema = TOOL_SCHEMAS[tool_name]

    try:
        validated = schema(**raw_arguments)
    except ValidationError as e:
        return {
            "error": "INVALID_INPUT",
            "message": e.errors()[0]["msg"] if e.errors() else str(e)
        }

    try:
        result = TOOL_FUNCTIONS[tool_name](**validated.model_dump())
    except Exception as e:
        return {
            "error": "TOOL_EXECUTION_FAILED",
            "message": str(e)
        }

    return result