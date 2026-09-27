"""
tools.py
--------
Real implementations of the agent's capabilities ("what the application
actually does"). These are plain Python functions operating on an
in-memory mock database, so the project runs with zero external
dependencies (no real DB / API needed to test it).

Errors are returned as *structured* dicts (e.g. {"error": "NOT_FOUND", ...})
rather than raised as raw exceptions where possible, so the agent can
observe the failure and decide what to do next (bonus: "Stronger Failure
Boundaries"). Truly unexpected exceptions are still allowed to raise and
are caught one layer up, in harness.safe_call.
"""

from typing import Any

_BOOKS: dict[int, dict[str, Any]] = {
    1: {"id": 1, "title": "Tum Teav", "author": "Preah Botumthera Som", "copies": 3},
    2: {"id": 2, "title": "Sophat", "author": "Rim Kin", "copies": 0},
    3: {"id": 3, "title": "Kolab Pailin", "author": "Nhok Them", "copies": 2},
    4: {"id": 4, "title": "Tep Sodachan", "author": "Nou Kan", "copies": 1},
}

def search_book(query: str) -> dict:
    """Search by title or author substring (case-insensitive)."""
    q = query.lower()
    matches = [
        {"id": b["id"], "title": b["title"], "author": b["author"]}
        for b in _BOOKS.values()
        if q in b["title"].lower() or q in b["author"].lower()
    ]
    if not matches:
        return {"error": "NOT_FOUND", "message": f"No books match '{query}'."}
    return {"results": matches}


def check_availability(book_id: int) -> dict:
    book = _BOOKS.get(book_id)
    if book is None:
        return {"error": "NOT_FOUND", "message": f"No book with id {book_id}."}
    return {"book_id": book_id, "title": book["title"], "copies_available": book["copies"]}


def borrow_book(book_id: int, member_id: str) -> dict:
    book = _BOOKS.get(book_id)
    if book is None:
        return {"error": "NOT_FOUND", "message": f"No book with id {book_id}."}
    if book["copies"] <= 0:
        return {"error": "OUT_OF_STOCK", "message": f"'{book['title']}' has no copies available."}
    book["copies"] -= 1
    return {
        "status": "BORROWED",
        "book_id": book_id,
        "title": book["title"],
        "member_id": member_id,
        "copies_remaining": book["copies"],
    }


def remove_book(book_id: int) -> dict:
    book = _BOOKS.get(book_id)
    if book is None:
        return {"error": "NOT_FOUND", "message": f"No book with id {book_id}."}
    del _BOOKS[book_id]
    return {"status": "REMOVED", "book_id": book_id, "title": book["title"]}


TOOL_FUNCTIONS = {
    "search_book": search_book,
    "check_availability": check_availability,
    "borrow_book": borrow_book,
    "remove_book": remove_book,
}