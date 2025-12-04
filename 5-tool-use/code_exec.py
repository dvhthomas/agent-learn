import argparse
import asyncio
import getpass
import logging
import os
from typing import List

import nest_asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent as ADKAgent
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

from common import add_verbose_argument, setup_logging

logger: logging.Logger = logging.getLogger(name=__name__)
_ = load_dotenv()

APP_NAME = "calculator"
USER_ID = "user1234"
SESSION_ID = "session_code_exec_async"


# Define the Agent
code_agent = LlmAgent(
    name="calculator_agent",
    model=str(os.environ.get("GOOGLE_MODEL")),
    code_executor=BuiltInCodeExecutor(),
    instruction="""You are a calculator agent.

    When given a mathematical expression, write and execute Python code
    to calculate the result.

    Return only the final numerical result as plain text, without
    markdown or code blocks.
    """,
    description="Executes Python code to perform calculations."
)

logger.info(f"Model: {code_agent.model}")

# Agent interaction (async)
async def call_agent_async(query: str) -> None:
    # Session and Runner
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    runner = Runner(
        agent=code_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    content = types.Content(
        role='user',
        parts=[
            types.Part(text=query),
        ]
    )

    print(f"\n--- Running Query: {query} ---")
    final_response = "No final text response captured."

    try:
        # Use run_async
        #
        # This is a pattern I don't see too often in Go: having the iterator
        # be a call to a function. Makes sense if the function is yielding
        # the iterator. Something I've seen more in C# as well.
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            print(f"Event ID: {event.id}, Author: {event.author}")

            # Check for specific parts first.
            has_specific_part = False

            # Notice that this loop only does something if the LLM is
            # returning the final result. We don't bother with interim steps.
            if event.content and event.content.parts and event.is_final_response:
                for part in event.content.parts:
                    # Logic specific to types of content in the current `part`
                    if part.executable_code:
                        # Access the actual code via `.code`
                        print(f"Debug: Agent generated code:\n```python\n{part.executable_code.code}\n```")
                        has_specific_part = True
                    elif part.code_execution_result:
                        # Access outcome and output correctly
                        print(f"Debug Code Execution Result: {part.code_execution_result.outcome} - Output:\n{part.code_execution_result.output}")
                        has_specific_part = True

                    elif part.text and not part.text.isspace:
                        # Also print any text parts in any event for debugging
                        print(f"Text: '{part.text.strip()}'")

                # Logic for all of the parts, regardless of part type
                text_parts = [part.text for part in event.content.parts if part.text]
                final_result = "".join(text_parts)
                print(f"==> Final Agent Response: {final_result}")

    except Exception as e:
       print(f"ERROR during agent run: {e}")

    print("-"*30)


async def main():
    await call_agent_async("Calculate the value of (5+7)*3")
    await call_agent_async("What is 10 factorial?")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool use example using CrewAI")
    add_verbose_argument(parser)

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        nest_asyncio.apply()
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR during agent run: {e}")
        # Handle specific error when running asyncio.run in an already running
        # loop (like Jupyter/Colab)
        if "cannot be called from a running event loop" in str(e):
            print("\nRunning in an existing event loop (like Colab/Jupyter).")
            print("Please run `await main()` in a notebook cell instead.")
            # If in an interactive environment like a notebook, you might need to run:await main()
        else:
            raise e # Re-raise other runtime errors
