import argparse
import asyncio
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)

# Set up logger
logger = logging.getLogger(__name__)

load_dotenv()

# API key must be set in the .env file via `load_dotenv()`
try:
    llm: Optional[ChatAnthropic] = ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL"), temperature=0.7
    )
except Exception as e:
    print(f"Error initializing language model: {e}")
    llm = None

# Define independent chains
# These three chains each represent distinct tasks that can be executed in parallel


def log_runnable(label: str) -> RunnableLambda:
    """Returns a RunnableLambda that logs the input with a given label and passes it through."""
    return RunnableLambda(lambda x: logger.info(f"Runnable '{label}' output: {x}") or x)


summarize_chain: Runnable = (
    ChatPromptTemplate.from_messages(
        [("system", "Summarize the following text concisely:"), ("user", "{topic}")]
    )
    | llm
    | StrOutputParser()
    | log_runnable("Summary")
)

questions_chain: Runnable = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Generate three interesting questions about the following topic:",
            ),
            ("user", "{topic}"),
        ]
    )
    | llm
    | StrOutputParser()
    | log_runnable("Questions")
)

terms_chain: Runnable = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Identify 5-10 key terms from the following topic, separated by commas:",
            ),
            ("user", "{topic}"),
        ]
    )
    | llm
    | StrOutputParser()
    | log_runnable("Key Terms")
)


# Build the parallel + Synthesis chain

# 1. Define the block of tasks to run in parallel. The results
# of these, along with the original topic, will be fed into the next step.

map_chain = RunnableParallel(
    {
        "summary": summarize_chain,
        "questions": questions_chain,
        "key_terms": terms_chain,
        "topic": RunnablePassthrough(),  # pass the original topic through
    }
)

# 2. Define the final synthesis prompt which will combine the parallel results.

synthesis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Based on the following information:
                Summary: {summary}
                Related Questions: {questions}
                Key Terms: {key_terms}
                Synthesize a comprehensive answer.""",
        ),
        ("user", "Original topic: {topic}"),
    ]
)

# 3. Construct the full chain by piping the parallel results directly
# into the synthesis prompt, followed by the LLM and output parser.

full_parallel_chain = map_chain | synthesis_prompt | llm | StrOutputParser()

# Run the Chain


async def run_parallel_chain(topic: str) -> None:
    """
    Asynchronously invokes the parallel processing chain with a specific topic
    and prints the synthesized result.
    Args:
        topic: The input topic to be processed by the LangChain chains."""
    if not llm:
        logger.error("LLM not initialized by the LangChain chains.")
        return

    logger.info(f"Running parallelLangChain example for topic: '{topic}'")

    try:
        # The input to `ainvoke` is the single topic string,
        # then passed to each runnable in the `map_chain`.
        response = await full_parallel_chain.ainvoke(topic)
        logger.info(f"---Synthesized final response--- \n\n{response}")
    except Exception as e:
        logger.error(f"Error occurred during chain execution: {e}")


async def main():
    """
    Main function to run the parallel LangChain example.
    Parses command-line arguments and kicks off the processing chain.
    """
    parser = argparse.ArgumentParser(description="Parallelization demo with LangChain")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging of LLM outputs",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="The history and future of space exploration",
        help="The topic to be processed by the LangChain chains.",
    )
    args = parser.parse_args()

    # Configure logging based on verbose flag
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s\n")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s\n")

    await run_parallel_chain(args.topic)


if __name__ == "__main__":
    asyncio.run(main())
