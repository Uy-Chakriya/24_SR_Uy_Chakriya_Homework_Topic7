"""
main.py
-------
Starts the application and accepts a user request from the command line.

Usage:
    python main.py --role member "Find a book about dragons and check if it's available"
    python main.py --role librarian "Remove the book Dune from the catalog"

Set ANTHROPIC_API_KEY in the environment to use the real Claude model.
Without it (or with USE_MOCK_LLM=1), a small deterministic mock LLM is
used instead so the agent loop, permissions, and safety checks can be
tested and graded without any API access.
"""

import argparse
import sys

from agent import Agent


def main():
    parser = argparse.ArgumentParser(description="Simple Safe Library Agent")
    parser.add_argument(
        "request",
        nargs="?",
        help="The user request in natural language. If omitted, an example run is used.",
    )
    parser.add_argument(
        "--role",
        choices=["member", "librarian"],
        default="member",
        help="Role to run the agent as (controls permissions). Default: member.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress step-by-step tool call logging.")
    args = parser.parse_args()

    user_request = args.request or "Find a book about dragons and check if it's available."

    print(f"=== Role: {args.role} ===")
    print(f"=== User request: {user_request} ===\n")

    agent = Agent(role=args.role, verbose=not args.quiet)
    answer = agent.run(user_request)

    print("\n=== Final answer ===")
    print(answer)


if __name__ == "__main__":
    sys.exit(main())
