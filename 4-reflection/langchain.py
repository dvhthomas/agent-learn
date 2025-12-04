import argparse
import logging
import os

from common import create_parser, setup_logging
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger: logging.Logger = logging.getLogger(__name__)  # type: ignore[attr-defined]
load_dotenv()


def run_reflection_loop():
    """
    Demonstrates a multi-step AI reflection loop to progressively
    improve a Python function.
    """

    # --- The Core Task ---
    task_prompt = """
    Your task is to create a Python function named `calculate_factorial`.
    The function should do the following:
        1. Accept a single integer `n` as input.
        2. Calculate its factorial (n!)
        3. Include a clear docstring explaining what the function does.
        4. Handle edge cases: The factorial of 0 is 1.
        5. Handle invalid input. Raise a ValueError if the input is a negative number.
    """

    # --- The Reflection Loop ---
    max_iterations = 3
    current_code = ""

    # We will build a conversation history to provide context in each step.
    # Use a List of HumanMessages.
    message_history = [HumanMessage(content=task_prompt)]

    for i in range(max_iterations):
        logger.info(
            "\n" + "=" * 25 + f" REFLECTION LOOP: ITERATION {i + 1} " + "=" * 25
        )

        # --- 1. Generate / Refine stage
        # In the first iteration, it generates. In subsequent iterations, it refines.
        if i == 0:
            logger.info("\n>>> STAGE 1: GENERATING initial code...")
            # The first message iso just the task prompt
            # Invoke accepts a sequence of message,string pairs
            # https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.llms.LLM.html#langchain_core.language_models.llms.LLM.invoke
            response = llm.invoke(message_history)
            current_code = response.content
        else:
            logger.info(">>> STAGE 2: REFINING code based on previous critique...")
            # The message history now contains the task, the last code, and the last critique.
            # Now we instruct the model to apply the critiques.
            message_history.append(
                HumanMessage(
                    content="Please refine the code using the critiques provided."
                )
            )
            response = llm.invoke(message_history)
            current_code = response.content
            logger.info(f"--- Generated Code v{i + 1}: ---\n{current_code}")

            message_history.append(response)

        # --- 2. REFLECT stage
        logger.info(">>> STAGE 2: REFLECTING on the generated code...")

        # Create a specific prompt for the reflector agent where it acts as a senior code reviewer.
        reflector_prompt = [
            SystemMessage(
                content="""
                You are a senior software engineer and an expert in Python.
                Your role is to perform a meticulous code review.
                Critically evaluate the provide Python code based on the original
                task requirements.
                Look for bugs, style issues, missing edge cases, and areas for improvement.
                If the code is perfect and meets all requirements,
                respond with the single phrase 'CODE_IS_PERFECT'.
                Otherwise, provide a bulleted list of your critiques.
                """
            ),
            HumanMessage(
                content=f"Original Task:\n{task_prompt}\n\nCode to Review:\n{current_code}"
            ),
        ]

        critique_response = llm.invoke(reflector_prompt)
        critique = critique_response.content

        # --- 3. STOPPING CONDITION
        if "CODE_IS_PERFECT" in critique:
            logger.info(
                "--- Critique ---\nNo further critiques found. The code is satisfactory."
            )
            break

        logger.info(f"--- Critique ---\n{critique}")
        message_history.append(
            HumanMessage(content=f"Critique of the previous code: \n{critique}")
        )

    print("\n" + "=" * 30 + " FINAL RESULT " + "=" * 30)
    print("\nFinal refined code after the reflection process:\n")
    print(current_code)


if __name__ == "__main__":
    parser = create_parser("Run reflection agents")
    args = parser.parse_args()

    setup_logging(args.verbose)

    logger.info("Running pipeline.")

    # Check if the API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. Add it to .env file."
        )

    # Use a lower temperature for more deterministic outputs.
    llm = ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        temperature=0.1,
    )
    run_reflection_loop()
