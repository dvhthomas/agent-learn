import argparse
import logging
import os
import uuid
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.events import Event
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types

# Load environment variables
load_dotenv()

# Set up logger
logger: logging.Logger = logging.getLogger(__name__)  # type: ignore[attr-defined]

# --- Define Tool Functions

# These functions simulate the actions of the specialist agents.


def booking_handler(request: str) -> str:
    """
    Handles booking requests for flights and hotels.
    Args:
        request: The user's request for a booking.
    Returns:
        A confirmation message that the booking was handled.
    """
    logger.info("-------------Booking Handler Called----------------")
    return f"Booking action for {request} was handled."


def info_handler(request: str) -> str:
    """
    Handles general information requests.
    Args:
        request: The user's question.
    Returns:
        A message indicating the information request was handled.
    """
    logger.info("-------------Info Handler Called----------------")
    return (
        f"Information request for '{request}'. Result: Simulated information retrieval."
    )


def unclear_handler(request: str) -> str:
    """
    Handles requests that could not be delegated.
    """
    logger.info("-------------Unclear Handler Called----------------")
    return f"Coordinator could not delegate request: '{request}'. Please clarify."


# -- Create Tools from Functions ---
booking_tool = FunctionTool(booking_handler)
info_tool = FunctionTool(info_handler)


def get_model_name() -> str:
    """Get the Google model name from environment variables."""
    model_name = os.getenv("GOOGLE_MODEL")
    if not model_name:
        raise ValueError("GOOGLE_MODEL environment variable is required")
    return model_name


# Define specialized sub-agents equipped with their respective tools
booking_agent = Agent(
    name="Booker",
    model=get_model_name(),
    description="A specialized agent that handles all flight and hotel booking requests by calling the booking tool.",
    tools=[booking_tool],
)

info_agent = Agent(
    name="Info",
    model=get_model_name(),
    description="A specialized agent that provides general information and answers user questions by calling the info tool.",
    tools=[info_tool],
)

# Define the parent agent with explicit delegation instructions

coordinator = Agent(
    name="Coordinator",
    model=get_model_name(),
    instruction="""
     You are the main coordinator. Your only task is to analyze incoming user requests.
     and delegate them to the appropriate specialist agent. Do not try to answer the user directly.\n
     - For any requests related to booking flights or hotels, delegate to the 'Booker' agent.\n
     - For all other general information questions, delegate to the 'Info' agent.
    """,
    description="A coordinator that routes user requests to the correct specialist agent.",
    sub_agents=[booking_agent, info_agent],
)


# --- Execution logic ---
async def run_coordinator(runner: InMemoryRunner, request: str) -> str:
    """Runs the coordinator agent with a given requests and delegates."""
    logger.info(f"\n---Running Coordinator with request: '{request}' ---")

    final_result: str = ""

    try:
        user_id = "user_123"
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )

        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=request)]),
        ):
            if event.is_final_response() and event.content:
                # Try to get text directly from event.content to avoid iterating over parts
                if hasattr(event.content, "text") and event.content.text:
                    final_result = str(event.content.text)
                elif event.content.parts:
                    # Fallback: iterated through parts and extract text (might trigger warning)
                    text_parts = [
                        part.text for part in event.content.parts if part.text
                    ]
                    final_result = "".join(text_parts)
                    # Assuming the loop should break after the final response
                    break

        logger.info(f"Coordinator Final Response: {final_result}")
        return final_result

    except Exception as e:
        logger.error(f"An error occurred while processing your request: {e}")
        return f"Sorry, an error occurred while processing your request: {e}."


async def main() -> None:
    """Main function to run the ADK example"""
    logger.info("---Google ADK Routing Example (ADK Auto-Flow Style)---")
    runner = InMemoryRunner(coordinator)

    # Example usage
    result_a = await run_coordinator(runner, "Book me a hotel in Paris.")
    logger.info(f"Final Output A: {result_a}")

    result_b = await run_coordinator(
        runner, "What is the highest mountain in the world?"
    )
    logger.info(f"Final Output B: {result_b}")

    result_c = await run_coordinator(runner, "Tell me a random fact.")
    logger.info(f"Final Output C: {result_c}")

    result_d = await run_coordinator(runner, "Find flights to Tokyo in the next month.")
    logger.info(f"Final Output D: {result_d}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Routing pattern demo with Google Agent Development Kit"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging of LLM outputs",
    )
    args = parser.parse_args()

    # Configure logging based on verbose flag
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    import asyncio

    asyncio.run(main())
