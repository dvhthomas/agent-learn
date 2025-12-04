import argparse
import asyncio
import logging
import os
import uuid

from common import create_parser, setup_logging
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.events import Event
from google.adk.tools import google_search
from google.genai import types

logger: logging.Logger = logging.getLogger(__name__)  # type: ignore[attr-defined]
_ = load_dotenv()

# Define state keys as constants to avoid typos
RENEWABLE_ENERGY_KEY = "renewable_energy_result"
EV_TECHNOLOGY_KEY = "ev_technology_result"
CARBON_CAPTURE_KEY = "carbon_capture_result"

# ---- Define Researcher Sub-Agents for Parallel Execution ----


renewable_energy_agent = LlmAgent(
    name="RenewableEnergyResearcher",
    model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp"),
    instruction="""You are an AI Research Assistant specializing in energy.
    Research the latest advancementts in 'renewable energy sources'.
    Use the Google Search tool provided. Summarize your key findings concisely
    (1-2 sentences). Output *only* the summary.""",
    description="Researches renewable energy sources.",
    tools=[google_search],
    output_key=RENEWABLE_ENERGY_KEY,
)

electric_vehicle_agent = LlmAgent(
    name="EVResearcher",
    model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp"),
    instruction="""You are an AI Research Assistant specializing in transportation.
    Research the latest developments in 'electric vehicle technology'.
    Use the Google Search tool provided. Summarize your key findings concisely
    (1-2 sentences). Output *only* the summary.""",
    description="Researches electric vehicles.",
    tools=[google_search],
    output_key=EV_TECHNOLOGY_KEY,
)

carbon_capture_agent = LlmAgent(
    name="CarbonCaptureResearcher",
    model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp"),
    instruction="""You are an AI Research Assistant specializing in climate solutions.
   Research the latest advancements in 'carbon capture methods'.
   Use the Google Search tool provided. Summarize your key findings concisely
   (1-2 sentences). Output *only* the summary.""",
    description="Researches carbon capture methods.",
    tools=[google_search],
    output_key=CARBON_CAPTURE_KEY,
)

# --- 2. Create the ParallelAgent that runs researchers concurrently
# This is the agent that orchestrations concurrent execution of the researchers.
# It finishes once all researchers have completed and stored their results in state.

parallel_research_agent = ParallelAgent(
    name="ParallelWebResearchAgent",
    sub_agents=[renewable_energy_agent, electric_vehicle_agent, carbon_capture_agent],
    description="Runs multiple research agents in parallel to gather information.",
)

# ---- Create the Synthesis Agent ----

synthesis_agent = LlmAgent(
    name="SynthesisAgent",
    model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp"),
    instruction=f"""You are an AI Research Assistant responsible for combining research
    findings into a structured report.

    Your primary task is to synthesize the following research summaries, clearly
    attributing findings to their source areas. Structure your response using headings
    for each topic. Ensure the report is coherent and integrates the key points smoothly.o
    **Crucially: your enitre report MUST be grounded *exclusively* on the information provided
    in the 'Input Summaries' below. Do NOT add any external knowledge, facts, or details
    not present in these specific summaries.**

    **Input Summaries:**

    * **Renewal Energy:**
      {{{RENEWABLE_ENERGY_KEY}}}
    * **Electric Vehicles:**
      {{{EV_TECHNOLOGY_KEY}}}
    * **Carbon Capture:**
      {{{CARBON_CAPTURE_KEY}}}

    **Output Format:**

    ## Summary of Recent Sustainable Technology advancements

    ### Renewable Energy Findings

    (Based on RenewableEnergyResearcher's findings)

    [Synthesize and elaborate *only* on the Renewable Energy input summary provided above.]

    ### Electric Vehicle Findings

    (Based on ElectricVehicleResearcher's findings)

    [Synthesize and elaborate *only* on the EV input summary provided above.]

    ### Carbon Capture Findings

    (Based on CarbonCaptureResearcher's findings)

    [Synthesize and elaborate *only* on the Carbon Capture input summary provided above.]

    ### Overall Conclustion

    [Provide a brief (1-2 sentence) concluding statement that connects *only*
    the finding presented above.]

    Output *only* the structured report following this format. Do no include any introductory
    or concluding phrases outside this structure, and strictly adhere to using only the
    provided input summary content.
    """,
    description="Combines research findings from parallel agents into a structured, cited report, strictly grounded on provided inputs.",
)

# --- 4. Create the SequentialAgent to orchestrate the overall flow.
# This is the main agent that will be run. It first executes the ParallelAgent
# to populated the state, and then executes the MergerAgent to produce the final
# output.

root_agent = SequentialAgent(
    name="ResearchAndSynthesisPipeline",
    sub_agents=[parallel_research_agent, synthesis_agent],
    description="Coordinates parallel research and synthesizes the results.",
)


def extract_content_text(event: Event) -> str | None:
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


async def run_pipeline(runner: InMemoryRunner) -> str | None:
    """Execute the research pipeline and return the final result."""
    # Create session
    user_id = "user_123"
    session_id = str(uuid.uuid4())
    _ = await runner.session_service.create_session(
        app_name=runner.app_name, user_id=user_id, session_id=session_id
    )

    # Process events from the pipeline
    final_result = None
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user", parts=[types.Part(text="Start the research pipeline")]
        ),
    ):
        if event.is_final_response():
            content = extract_content_text(event)
            if content:
                final_result = content

    return final_result


async def main():
    """Main entry point: setup logging and run the research pipeline."""
    parser = create_parser("Run a pipeline of research agents.")
    args = parser.parse_args()

    setup_logging(args.verbose)

    logger.info("Running research pipeline.")
    runner = InMemoryRunner(root_agent)

    final_result = await run_pipeline(runner)

    if final_result:
        print(f"Final synthesized response:\n{final_result}")
    else:
        logger.error("No final result received from pipeline.")


if __name__ == "__main__":
    asyncio.run(main())
