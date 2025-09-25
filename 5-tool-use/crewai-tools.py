import argparse
import logging
import os
import sys

from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool
from dotenv import load_dotenv

from common import add_verbose_argument, setup_logging

logger: logging.Logger = logging.getLogger(name=__name__)
load_dotenv()
STOCK_PRICE_TOOL : str = "Stock Price Lookup Tool"

@tool(STOCK_PRICE_TOOL)
def get_stock_price(ticker: str) -> float:
    """
    Get the current stock price for a given ticker symbol.
    Raises a ValueError if the ticker is not found.
    """
    logger.info(f"Tool Call: get_stock_price({ticker})")
    simulated_prices = {
        "AAPL": 178.15,
        "GOOGL": 1750.30,
        "MSFT": 425.50,
    }

    price = simulated_prices.get(ticker)
    if price is None:
        # Raising a specific error is better than returning a string
        # because agents are equipped to handle exceptions to decide
        # on the next action.
        raise ValueError(f"Simulated price for ticker '{ticker.upper()}' not found")
    return price

# --- 2. Define the Agent ---

# Create the LLM configuration first
llm = LLM(
    model=f"anthropic/{os.environ.get('ANTHROPIC_MODEL')}",
    api_key=os.environ.get('ANTHROPIC_API_KEY')
)

# The agent definition remains the same, but it will now leverage the improved tool.
financial_analyst_agent = Agent(
    role='Senior Financial Analyst',
    goal='Analyze stock data using provided tools and report key prices.',
    backstory="You are an experienced financial analyst adept at using data sources to find stock information. You provide clear, direct answers.",
    verbose=True,
    tools=[get_stock_price],
    llm=llm,  # Add this line to use Anthropic instead of OpenAI
    # Allowing delegation can be useful, but is not necessary for this simply task.Agent
    allow_delegation=False
)

# --- 3. Refined Task: Clearer Instructions and Error Handling ---
# The task description is more specific and guides the agent on how to react
# to both successful data  retrieval and potential errors.
analyze_aapl_task = Task(
    description=(
        "What is the current simulated stock price for Apple (ticker: AAPL)?"
        f"Use the '{STOCK_PRICE_TOOL}' to find it."
        "If the ticker is not found, you must report that you were unable to retrieve the price."
    ),
    expected_output=(
        "A single, clear sentence stating the simulated stock price for AAPL."
        "For example: 'The stimulated stock price for AAPL is $178.15.'"
        "If the price cannont be found, state that clearly."

    ),
    agent=financial_analyst_agent,
)

# -- 4. Formulate the Crew ---
# The crew orchestrates how the agent and task work together.
financial_crew = Crew(
    agents=[financial_analyst_agent],
    tasks=[analyze_aapl_task],
    manager_llm=llm,
    verbose=True #Set to False for less detailed production logs.
)

# -- 5. Run the Crew within a Main execution block ---
def main():
    """Main function to run the crew """
    if not os.environ.get("ANTHROPIC_API_KEY") or not os.environ.get("ANTHROPIC_MODEL"):
        logger.warning("ANTHROPIC_API_KEY or ANTHROPIC_MODEL environment variable is not set. Try adding a .env file.")
        print("ERROR: ANTHROPIC_API_KEY or ANTHROPIC_MODEL environment variable is not set.", file=sys.stderr)
        return

    print("\n## Starting the Financial Crew")
    print("-"*20)
    result = financial_crew.kickoff()
    print("-"*20)
    print("Crew execution finished")
    print("\nFinal Result:\n", result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool use example using CrewAI")
    add_verbose_argument(parser)

    args = parser.parse_args()
    setup_logging(args.verbose)

    main()
