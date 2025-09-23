import os
import argparse
import logging
from common import setup_logging, add_verbose_argument
from dotenv import load_dotenv

from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
import uuid
import asyncio

logger = logging.getLogger(__name__)
load_dotenv()

# The first agent generates an initial draft
generator = LlmAgent(
    name="draft_writer",
    model=os.getenv("GOOGLE_MODEL"),
    instruction="Write a comprehensive paragraph about the given subject, including relevant details, dates, and key figures where applicable.",
    description="Generates an initial draft on a given subject",
    output_key="draft_text",  # the output is saved to this state key.
)

# The second agent critiques the draft from the first agent.
reviewer = LlmAgent(
    name="fact_checker",
    model=os.getenv("GOOGLE_MODEL"),
    description="Reviews a given text for factural accuracy and provides a structured critique.",
    instruction="""
    You are a meticulous fact checker.
    1. Read the text provided in the state key 'draft_text'.
    2. Carefuly verify the factual accuracy of all claims.
    3. Your final output must be a dictionary containing two keys:
        - "status": A string, either "ACCURATE" or "INACCURATE".
        - "reasoning": A string providing a clear explanation for your status,
           citing specific issues if any are found.
    """,
    output_key="review_output",  # The structured dictionary is saved here.
)

review_pipeline = SequentialAgent(
    name="WriteAndReviewPipeline",
    sub_agents=[generator, reviewer],
)


# Execution Flow:
# 1. generator runs -> saves its paragraph to state['draft_text'].
# 2. reviewer runs -> reads state['draft_text'] and saves its dictionary output to state['review_output'].


def extract_content_text(event) -> str | None:
    """Extract text content from an ADK event, handling both formats."""
    if not event.content:
        return None

    # Try direct text property first (newer format)
    if hasattr(event.content, "text") and event.content.text:
        return event.content.text

    # Fall back to parts extraction (multimodal format)
    if event.content.parts:
        text_parts = [part.text for part in event.content.parts if part.text]
        return "".join(text_parts)

    return None


async def run_pipeline(topic: str):
    """Execute the review pipeline and show results."""
    runner = InMemoryRunner(review_pipeline)

    try:
        # Create session
        user_id = "user_123"
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )

        # Process events from the pipeline
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=topic)]),
        ):
            if event.is_final_response():
                content = extract_content_text(event)
                if content:
                    logger.notice(f"\n=== FINAL RESULT ===\n{content}")
            else:
                # Log intermediate results
                content = extract_content_text(event)
                if content:
                    logger.notice(f"\n=== INTERMEDIATE RESULT ===\n{content}")
    finally:
        # Clean up the runner to close HTTP connections
        if hasattr(runner, "close"):
            await runner.close()

    logger.notice("=== PIPELINE COMPLETE ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run reflection agents")
    add_verbose_argument(parser)
    parser.add_argument(
        "--topic",
        "-t",
        type=str,
        default="The causes of the French Revolution",
        help="The topic to be processed by the agents.",
    )
    args = parser.parse_args()
    setup_logging(args.verbose)

    logger.notice("Running write and review pipeline.")

    # Check if the API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set. Add it to .env file."
        )

    # Run the pipeline using InMemoryRunner
    logger.notice(f"=== STARTING PIPELINE EXECUTION with topic: '{args.topic}' ===")
    asyncio.run(run_pipeline(args.topic))
