import os
import json

from schemas import anthropic_tool_definitions
from harness import safe_call, MAX_TOOL_CALLS

SYSTEM_PROMPT = (
    "You are a library assistant agent. You help users search for books, "
    "check availability, borrow books, and (librarians only) remove books "
    "from the catalog. Use the available tools to gather real information "
    "before answering — never guess book IDs or availability. When you have "
    "enough information, give a short, final natural-language answer to the "
    "user and stop calling tools."
)


class Agent:
    def __init__(self, role: str, model: str = "claude-sonnet-4-6", verbose: bool = True):
        self.role = role
        self.model = model
        self.verbose = verbose
        self.use_mock = os.environ.get("USE_MOCK_LLM") == "1" or not os.environ.get("ANTHROPIC_API_KEY")

        if not self.use_mock:
            import anthropic
            self.client = anthropic.Anthropic()

    def log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def run(self, user_request: str) -> str:
        messages = [{"role": "user", "content": user_request}]
        tool_calls_made = 0

        while True:
            if tool_calls_made >= MAX_TOOL_CALLS:
                return (
                    "Stopping: reached the maximum number of tool calls "
                    f"({MAX_TOOL_CALLS}) for this request without a final answer."
                )

            response = self._call_llm(messages)

            text_parts, tool_use = self._parse_response(response)

            if tool_use is None:
                final_text = "\n".join(text_parts).strip()
                return final_text or "(no answer produced)"

            tool_name = tool_use["name"]
            tool_args = tool_use["input"]
            self.log(f"[agent] -> calling tool: {tool_name}({tool_args})")

            result = safe_call(self.role, tool_name, tool_args)
            tool_calls_made += 1
            self.log(f"[agent] <- tool result: {result}")

            messages.append({"role": "assistant", "content": response["raw_content"]})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use["id"],
                            "content": json.dumps(result),
                        }
                    ],
                }
            )

    def _call_llm(self, messages: list[dict]) -> dict:
        if self.use_mock:
            return self._mock_llm(messages)

        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=anthropic_tool_definitions(),
            messages=messages,
        )
        return {
            "raw_content": [b.model_dump() for b in resp.content],
            "stop_reason": resp.stop_reason
        }

    def _parse_response(self, response: dict):
        text_parts = []
        tool_use = None

        for block in response["raw_content"]:
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use" and tool_use is None:
                tool_use = block

        return text_parts, tool_use

    def _mock_llm(self, messages: list[dict]) -> dict:
        user_request = messages[0]["content"]
        lower = user_request.lower()

        tool_results_seen = [
            m for m in messages
            if m["role"] == "user" and isinstance(m["content"], list)
        ]

        step = len(tool_results_seen)

        def text_response(msg: str) -> dict:
            return {
                "raw_content": [{"type": "text", "text": msg}],
                "stop_reason": "end_turn"
            }

        def tool_call(name: str, args: dict) -> dict:
            block = {
                "type": "tool_use",
                "id": f"mock_{name}_{step}",
                "name": name,
                "input": args
            }

            return {
                "raw_content": [block],
                "stop_reason": "tool_use"
            }

        if step == 0:
            for kw in [
                "tum teav",
                "sophat",
                "kolab pailin",
                "pailin",
                "tep sodachan",
                "sodachan"
            ]:
                if kw in lower:
                    return tool_call("search_book", {"query": kw})

            return tool_call(
                "search_book",
                {"query": user_request.split()[-1]}
            )

        last_result_raw = tool_results_seen[-1]["content"][0]["content"]
        last_result = json.loads(last_result_raw)

        if step == 1:
            if "error" in last_result:
                return text_response(
                    f"I couldn't find that book: {last_result.get('message')}"
                )

            book_id = last_result["results"][0]["id"]

            return tool_call(
                "check_availability",
                {"book_id": book_id}
            )

        if step == 2:
            if "error" in last_result:
                return text_response(
                    f"I couldn't check availability: {last_result.get('message')}"
                )

            book_id = last_result["book_id"]

            if "delete" in lower or "remove" in lower:
                return tool_call(
                    "remove_book",
                    {"book_id": book_id}
                )

            if "borrow" in lower or "check out" in lower:
                return tool_call(
                    "borrow_book",
                    {
                        "book_id": book_id,
                        "member_id": "member_001"
                    }
                )

            return text_response(
                f"'{last_result['title']}' has "
                f"{last_result['copies_available']} copies available."
            )

        if "error" in last_result:
            return text_response(
                f"That action failed: {last_result.get('message')} "
                f"({last_result.get('error')})"
            )

        if last_result.get("status") == "BORROWED":
            return text_response(
                f"Done! '{last_result['title']}' has been borrowed "
                f"for {last_result['member_id']}. "
                f"{last_result['copies_remaining']} copies remain."
            )

        if last_result.get("status") == "REMOVED":
            return text_response(
                f"Done! '{last_result['title']}' was removed from the catalog."
            )

        return text_response("Here is what I found.")