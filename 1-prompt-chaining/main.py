import logging
import os

from common import init
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


def main():
    init()  # Initialize logging with defaults
    """
    Main function that demonstrates prompt chaining using LangChain.

    This function creates a two-step chain:
    1. Extract technical specifications from input text
    2. Transform the extracted specifications into a structured JSON format

    The chain processes hardware specification text and outputs a JSON object
    with standardized keys for CPU, memory, and storage information.

    Sample output:
    ```json
    {
      "cpu": "Intel Core i7-12700K",
      "memory": "16GB DDR4 RAM",
      "storage": "512GB SSD"
    }
    ```
    """
    load_dotenv()

    model_name = os.getenv("ANTHROPIC_MODEL")
    if not model_name:
        raise ValueError("ANTHROPIC_MODEL environment variable is required")

    llm = ChatAnthropic(
        model=model_name,
        temperature=0.0,  # don't get creative!
    )

    prompt_extract = ChatPromptTemplate.from_template(
        "Extract the technical specification from the following text:\n\n{text_input}"
    )

    prompt_trans = ChatPromptTemplate.from_template(
        "Translate the following specifications into a JSON object with 'cpu', 'memory', and 'storage' as keys:\n\n{specifications}"
    )

    # Put together the prompt chain using LangChain expression library (LCEL)
    # The StrOutputParser() converts the LLM's message output to a simple string.
    extraction_chain = prompt_extract | llm | StrOutputParser()

    # The full chain passes the output of the extraction chain to the translation chain
    full_chain = (
        {"specifications": extraction_chain} | prompt_trans | llm | StrOutputParser()
    )

    # Run the chain
    input_text = "Intel Core i7-12700K, 16GB DDR4, 512GB SSD"
    final_result = full_chain.invoke({"text_input": input_text})
    print(final_result)


if __name__ == "__main__":
    main()
