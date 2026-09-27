"""
schemas.py
----------
Explicit input schemas for every tool the agent can call.

Each schema is a Pydantic model. Pydantic gives us:
  1. A machine-readable JSON Schema we hand to the LLM so it knows
     exactly what arguments a tool expects (names, types, required fields).
  2. Runtime validation: if the model (or a bug) sends bad arguments,
     Pydantic raises a ValidationError *before* any business logic runs.

This is "Tool Schema" from the assignment (2B) and also backs part of
"Basic input validation" (2D).
"""

from pydantic import BaseModel, Field, field_validator


class SearchBookInput(BaseModel):
    query: str = Field(..., description="Title, author, or keyword to search for.")

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query must not be empty")
        return v.strip()


class CheckAvailabilityInput(BaseModel):
    book_id: int = Field(..., description="The numeric ID of the book to check.")

    @field_validator("book_id")
    @classmethod
    def positive_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("book_id must be a positive integer")
        return v


class BorrowBookInput(BaseModel):
    book_id: int = Field(..., description="The numeric ID of the book to borrow.")
    member_id: str = Field(..., description="The ID of the member borrowing the book.")

    @field_validator("book_id")
    @classmethod
    def positive_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("book_id must be a positive integer")
        return v

    @field_validator("member_id")
    @classmethod
    def member_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("member_id must not be empty")
        return v.strip()


class RemoveBookInput(BaseModel):
    book_id: int = Field(..., description="The numeric ID of the book to remove from the catalog.")

    @field_validator("book_id")
    @classmethod
    def positive_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("book_id must be a positive integer")
        return v


TOOL_SCHEMAS = {
    "search_book": SearchBookInput,
    "check_availability": CheckAvailabilityInput,
    "borrow_book": BorrowBookInput,
    "remove_book": RemoveBookInput,
}

TOOL_DESCRIPTIONS = {
    "search_book": "Search the library catalog by title, author, or keyword. Returns a list of matching books with their IDs.",
    "check_availability": "Check how many copies of a specific book (by book_id) are currently available to borrow.",
    "borrow_book": "Borrow a copy of a book for a member. Reduces available copies by one. Requires member permission.",
    "remove_book": "Permanently remove a book from the catalog. Destructive action, restricted to librarians.",
}


def anthropic_tool_definitions() -> list[dict]:
    """
    Build the `tools` list in the format the Anthropic Messages API expects:
    [{"name": ..., "description": ..., "input_schema": <JSON Schema>}, ...]
    """
    tools = []
    for name, model in TOOL_SCHEMAS.items():
        schema = model.model_json_schema()
        schema.pop("title", None)
        tools.append(
            {
                "name": name,
                "description": TOOL_DESCRIPTIONS[name],
                "input_schema": schema,
            }
        )
    return tools
