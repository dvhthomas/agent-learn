import argparse
import asyncio
import logging
import os

import nest_asyncio
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from common import add_verbose_argument, setup_logging

load_dotenv()
logger = logging.getLogger(__name__)


try:
    llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"), temperature=0)
except Exception as e:
    logger.error(f"🔴 Error initializing language model: {e}")
    llm = None


@tool
def search_information(query: str) -> str:
    """
    Provies factual information on a given topic.
    Use this tool to find answers to phrases like 'capital of France'
    or 'weather in London?'.
    """
    logger.notice(f"--- 🔎 Tool Called: search_information with query: '{query}' ---")

    # Simulate a search tool with a dictionary of predefined results.
    simulated_results = {
        "weather in london": "The weather in London is currently cloudy with a temperature of 15°C.",
        "capital of france": "The capital of France is Paris.",
        "population of earth": "The estimated population of Earth is around 8 billion people.",
        "tallest mountain": "Mount Everest is the tallest mountain above sea level.",
        "default": f"Simulated search result for '{query}': No specific information found, but the topic seems interesting.",
    }

    result = simulated_results.get(query.lower(), simulated_results["default"])
    logger.notice(f"--- 🔎 Tool Result: '{result}' ---")
    return result


tools = [search_information]

# --- Create a Tool-Calling Agent ---

if llm:
    agent_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            ("human", "{input}"),
            # See README.md for more on the `agent_scratchpad`
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

# Create the agent, binding the LLM, tools, and prompt together
# What it does**:
# 1. Binds the LLM with the tools, enabling the model to generate tool calls
# 2. Creates an agent that can reason about when to use tools
# 3. Formats the prompt to include the agent's scratchpad for tracking tool usage history
# 4. Returns a runnable agent object that can be executed by an AgentExecutor
#
# **Result**: An agent that can interpret user queries, decide which tools to use,
# call those tools, and incorporate the results into its responses.
# The agent handles the reasoning loop of: analyze query → decide on tool → call tool →
# incorporate result → respond to user.
agent = create_tool_calling_agent(llm, tools, agent_prompt)

# AgentExecutor is the runtime that invokes the agent and executes The
# chosen tools.
# The 'tools' agrument is not needed here as they are already bound to the agent.
agent_executor = AgentExecutor(agent=agent, verbose=True, tools=tools)


async def run_agent_with_tool(query: str) -> str:
    """Invokes the agent executor with a query and prints the final response."""
    logger.notice(f"--- 🤖 Running Agent with Query: '{query}' ---")
    try:
        response = await agent_executor.ainvoke({"input": query})
        logger.notice(f"--- 🤖 Final Agent Response: '{response}' ---")
        print(response["output"])
    except Exception as e:
        logger.error(f"An error occurred during agent execution: {e}")

    return response


async def main():
    """Runs all agent queries concurrently."""
    tasks = [
        run_agent_with_tool("What is the capital of France?"),
        run_agent_with_tool("What's the weather like in London?"),
        run_agent_with_tool("Tell me something about dogs."),
    ]

    """
    `await asyncio.gather(*tasks)` runs multiple async operations concurrently and waits for all of them to complete.

    Breaking it down:

    1. **`tasks`**: A list of coroutines (async function calls) - in this case, 3 calls to `run_agent_with_tool()` with different queries
    2. **`*tasks`**: Unpacks the list, passing each coroutine as a separate argument to `gather()`
    3. **`asyncio.gather()`**: Runs all coroutines concurrently and waits for all to finish
    4. **`await`**: Waits for the entire gather operation to complete

    Instead of running the 3 agent queries sequentially (which would take longer), this executes all 3 queries simultaneously,
    making the program faster by leveraging async concurrency.
    """
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run reflection agents")
    add_verbose_argument(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    nest_asyncio.apply()
    asyncio.run(main())
