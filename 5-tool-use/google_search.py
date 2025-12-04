# Starting point for most scripts with logging, CLI arg setup, and environment.
# Create a .env file in the same directory as the script
import argparse
import asyncio
import logging
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

from common import add_verbose_argument, setup_logging

logger : logging.Logger = logging.getLogger(__name__)
_ = load_dotenv()

# Define variables required for Session setup and Agent execution
# All of the Google ADK tools operate in the context of a session.
APP_NAME = "Google_Search_agent"
USER_ID = "user1234"
SESSION_ID = "1234"

#Define Agent with access to search tool
root_agent = Agent(
    name="basic_search_agent",
    model=str(os.environ.get("GOOGLE_MODEL")),
    description="Agent to answer questions using Google Search",
    instruction="I can answer you questions by searching the internet. Just ask me anything!",
    tools=[google_search] # Pre-build tool to perform Google searches
)

# Agent interaction
async def call_agent(query: str):
    session_service = InMemorySessionService()
    _ = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)
    content = types.Content(role='user',parts=[types.Part(text=query)])


    final_response = "No response"
    # `run_async` is key here. The original code called for `run` and that resulted in
    # warnings:
    # <sys>:0: RuntimeWarning: coroutine 'AsyncClient.aclose' was never awaited
    #    RuntimeWarning: Enable tracemalloc to get the object allocation traceback
    #               ERROR    Task was destroyed but it is pending!
    #                        task: <Task pending name='Task-6' coro=<AsyncClient.aclose() running at
    #                        /Users/bitsbyme/projects/agent-learn/5-tool-use/.venv/lib/python3.13/site-packages/httpx/_
    #                        client.py:1978>>
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            # Check if content or parts are None/empty to avoid AttributeError
            if not event.content or not event.content.parts:
                logger.warning("The call to Google Search failed to return any content.")
            else:
                # Extract text from the first part of the response
                final_response = str(event.content.parts[0].text)
            print("Agent Response: ",final_response)



async def main():
    await call_agent("What's the latest AI news")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Brief description of the script's purpose"
    )
    add_verbose_argument(parser)
    args = parser.parse_args()
    setup_logging(int(args.verbose))

    asyncio.run(main())
