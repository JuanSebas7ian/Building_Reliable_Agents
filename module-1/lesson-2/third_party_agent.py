from typing import Any, Dict, List
from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

client = wrap_openai(OpenAI())

@traceable(run_type="tool")
def weather_retriever():
    """Retrieve current weather information."""
    return "It is sunny today"

# Define the tool schema for OpenAI
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "weather_retriever",
        "description": "Get the current weather conditions",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

@traceable
def agent(question: str) -> Dict[str, Any]:
    messages: List[Any] = [{"role": "user", "content": question}]
    tools: List[Any] = [WEATHER_TOOL]

    # First API call with tool available
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    # Handle tool calls if the model wants to use them
    if response_message.tool_calls:
        # Add assistant's tool call to messages
        tool_calls_payload: List[Dict[str, Any]] = []
        for tc in response_message.tool_calls:
            tc_fn: Any = getattr(tc, "function", None)
            tool_calls_payload.append({
                "id": getattr(tc, "id", ""),
                "type": getattr(tc, "type", "function"),
                "function": {
                    "name": getattr(tc_fn, "name", ""),
                    "arguments": getattr(tc_fn, "arguments", "{}")
                }
            })

        messages.append({
            "role": "assistant",
            "content": response_message.content or "",
            "tool_calls": tool_calls_payload
        })

        # Execute the tool call(s)
        for tool_call in response_message.tool_calls:
            tc_fn: Any = getattr(tool_call, "function", None)
            fn_name = getattr(tc_fn, "name", "") if tc_fn else ""
            if fn_name == "weather_retriever":
                result = weather_retriever()

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": getattr(tool_call, "id", ""),
                    "name": "weather_retriever",
                    "content": result
                })

        # Make second API call with tool results
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        response_message = response.choices[0].message

    final_content = response_message.content or ""
    messages.append({"role": "assistant", "content": final_content})
    return {"messages": messages, "output": final_content}

if __name__ == "__main__":
    result = agent("What is the weather today?")
    print(result.get("output", ""))
