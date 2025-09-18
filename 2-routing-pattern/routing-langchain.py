import argparse
import json
import logging
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
)
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


# Set up logger
logger = logging.getLogger(__name__)


def log_llm_output(output, step_name):
    """Log LLM output at DEBUG level"""
    logger.debug(f"\n=== {step_name} LLM OUTPUT ===")
    logger.debug(f"Type: {type(output)}")
    logger.debug(f"Raw output: {repr(output)}")
    if hasattr(output, "content"):
        logger.debug(f"Content: {output.content}")
    if hasattr(output, "response_metadata"):
        logger.debug(
            f"Response metadata: {json.dumps(output.response_metadata, indent=2, default=str)}"
        )
    logger.debug("=== END LLM OUTPUT ===\n")


def booking_handler(request: str) -> str:
    """Simulates the Booking Agent handling a request"""
    logger.info("Delegating to booking handler")
    return f"Booking handler processed request: {request} Result: Simulated booking action."


def info_handler(request: str) -> str:
    """Simulates the Info Agent handling a request"""
    logger.info("Delegating to info handler")
    return f"Info handler processed request: {request} Result: Simulated information retrieval."


def unclear_handler(request: str) -> str:
    """Simulates the Unclear Agent handling a request"""
    logger.info("Delegating to unclear handler")
    return f"Coordinator could not delegate request: {request} Please clarify."


try:
    llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL"), temperature=0.0)
    logger.info(f"Language model initialized: {llm.model}")
except Exception as e:
    logger.error(f"Error initializing language model: {e}")
    llm = None

# Define Coordinator Router Chain

# First, the chain decides which handler to delegate to

coordinator_router_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Analyze the user's request and determine which specialist handler should process it.

                - if the request is related to booking flights or hotels, output 'booker'.
                - for all other general information questions, output 'info'.
                - if the request is unclear or doesn't fit either category, output 'unclear'.

                ONLY output one word: 'booker', 'info', or 'unclear'.
            """,
        ),
        ("user", "{request}"),
    ]
)

if llm:

    def log_and_parse(output):
        log_llm_output(output, "COORDINATOR_ROUTER")
        return StrOutputParser().invoke(output)

    coordinator_router_chain = coordinator_router_prompt | llm | log_and_parse

    # ---Define the delegation logic, which is equivalent to ADK's Auto-Flow based on sub_agents) ---

    # Use RunnableBranch to route based on the router chain's output

    branches = {
        "booker": RunnablePassthrough.assign(
            output=lambda x: booking_handler(x["request"]["request"])
        ),
        "info": RunnablePassthrough.assign(
            output=lambda x: info_handler(x["request"]["request"])
        ),
        "unclear": RunnablePassthrough.assign(
            output=lambda x: unclear_handler(x["request"]["request"])
        ),
    }

# Create the RunnableBranch. It takes the output of the router chain `coordinator_router_chain`
# and routes the original input (`request`) to the corresponding handler.
delegation_branch = RunnableBranch(
    (lambda x: x["decision"].strip() == "booker", branches["booker"]),
    (lambda x: x["decision"].strip() == "info", branches["info"]),
    branches["unclear"],  # Default branch for 'unclear' or any other output
)


# Combine the router chain and the delegation branch into a single runnable.
#
# The router chain's output ('decision') is passed along with the original input ('request')
# to the `delegation_branch`.


# Create the coordinator agent
coordinator_agent = (
    {"decision": coordinator_router_chain, "request": RunnablePassthrough()}
    | delegation_branch
    | (lambda x: x["output"])  # extract the final output
)


def main():
    if not llm:
        logger.warning("Skipping agent execution due to LLM initialization failure.")
        return

    logger.info("--- Running with a booking request")
    request_a = "Book me a flight to London"
    result_a = coordinator_agent.invoke({"request": request_a})
    logger.info(f"Final Result: {result_a}")

    logger.info("--- Running with an info request")
    request_b = "What is the capital of Italy?"
    result_b = coordinator_agent.invoke({"request": request_b})
    logger.info(f"Final Result: {result_b}")

    logger.info("--- Running with an unclear request")
    request_c = "Not a helpful request"
    result_c = coordinator_agent.invoke({"request": request_c})
    logger.info(f"Final Result: {result_c}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Routing pattern demo with LangChain")
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

    main()
