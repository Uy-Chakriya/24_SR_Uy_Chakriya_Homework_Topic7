# Simple Safe Library Agent

A small agentic application for Topic 07: **Autonomous Agents & Tool Integration**.

The agent receives a natural-language library request, decides which tool to use, executes the tool through a safety layer, observes the result, and returns a final answer.

## 1. Project Overview

The agent supports two roles:

* `member`
* `librarian`

Example requests:

* "Find Kolab Pailin and check if it's available."
* "I want to borrow Tum Teav."
* "Remove Sophat from the catalog." *(librarian only)*

The mock catalog contains:

* Tum Teav
* Sophat
* Kolab Pailin
* Tep Sodachan

The **LLM only proposes tool calls**. `harness.py` controls whether the tool is actually allowed to execute.

## 2. Available Tools

| Tool                              | Purpose                                   |
| --------------------------------- | ----------------------------------------- |
| `search_book(query)`              | Search books by title, author, or keyword |
| `check_availability(book_id)`     | Check available copies                    |
| `borrow_book(book_id, member_id)` | Borrow a book                             |
| `remove_book(book_id)`            | Remove a book *(librarian only)*          |

Tool implementations are in `tools.py`, while Pydantic input schemas are in `schemas.py`.

## 3. Agent Flow

```text
User Request
    ↓
Agent / LLM
    ↓
Tool Call Proposed
    ↓
harness.safe_call()
    ↓
Permission Check
    ↓
Input Validation
    ↓
Tool Execution
    ↓
Tool Result
    ↓
Agent Decides Again
    ↓
Another Tool OR Final Answer
```

Every tool call goes through `harness.safe_call()`. The model never directly executes `tools.py`.

## 4. Permission Control

| Action               | Member | Librarian |
| -------------------- | :----: | :-------: |
| `search_book`        |    ✓   |     ✓     |
| `check_availability` |    ✓   |     ✓     |
| `borrow_book`        |    ✓   |     ✓     |
| `remove_book`        |    ✗   |     ✓     |

If a member tries to remove a book, the harness returns:

```python
{
    "error": "PERMISSION_DENIED",
    "message": "..."
}
```

The book is not deleted.

## 5. Safety Controls

`harness.py` provides:

* **Permission checking** — controls which role can use each tool.
* **Input validation** — validates arguments using Pydantic schemas.
* **Error handling** — returns structured errors such as:

  * `UNKNOWN_TOOL`
  * `PERMISSION_DENIED`
  * `INVALID_INPUT`
  * `TOOL_EXECUTION_FAILED`
  * `NOT_FOUND`
  * `OUT_OF_STOCK`
* **Tool-call limit** — `MAX_TOOL_CALLS = 6` prevents endless loops.

## 6. Example

```bash
USE_MOCK_LLM=1 python3 main.py --role member "Find the book Kolab Pailin and check if it's available"
```

Example flow:

```text
search_book("kolab pailin")
        ↓
check_availability(book_id=3)
        ↓
"Kolab Pailin has 2 copies available."
```

Permission testing:

```bash
USE_MOCK_LLM=1 python3 main.py --role member "Remove the book Sophat from the catalog"

USE_MOCK_LLM=1 python3 main.py --role librarian "Remove the book Sophat from the catalog"
```

## 7. Project Structure

```text
library-agent/
├── README.md
├── requirements.txt
├── main.py
├── agent.py
├── tools.py
├── schemas.py
└── harness.py
```

* `main.py` — CLI entry point
* `agent.py` — agent loop and LLM interaction
* `tools.py` — tool implementations and mock database
* `schemas.py` — Pydantic schemas and tool definitions
* `harness.py` — permissions, validation, error handling, and limits

## 8. Run

Install dependencies:

```bash
pip install -r requirements.txt
```

### Mock Mode

No API key or network is required:

```bash
USE_MOCK_LLM=1 python3 main.py --role member "Find Kolab Pailin"
```

### Real Claude Mode

```bash
export ANTHROPIC_API_KEY=your_key_here
python3 main.py --role librarian "Check if Dune is available"
```

Use `--role member` or `--role librarian` to test permissions.

Use `--quiet` to hide tool-call logs.

## 9. Key Design

The main safety principle is:

```text
LLM proposes → Harness validates → Tool executes
```

This keeps **permission, validation, and error handling in application code**, rather than relying only on the LLM prompt.
