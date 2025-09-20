# Parallelization

## LangChain

A key element of LangChain is `ainvoke` within the `async def` function.
In this specific script, `full_parallel_chain.ainvoke(topic)` triggers the parallel execution of `summarize_chain`, `questions_chain`, and `terms_chain` with the provided `topic`, and then synthesizes their outputs.

Per Gemini:

> `ainvoke` is a method used to **asynchronously** execute a LangChain "runnable" (in this case, `full_parallel_chain`).
>
> The `a` prefix in `ainvoke` stands for "asynchronous".
This means it's a non-blocking call that is awaited, allowing other tasks to run while the chain is being executed.
It's the asynchronous equivalent of the `invoke` method.

### Logging

I wanted to see what each of the Runnables was doing and Gemini proposed adding a RunnableLambda function to the LangChain chain:


```py
# These three chains each represent distinct tasks that can be executed in parallel

def log_runnable(label: str) -> RunnableLambda:
    """Returns a RunnableLambda that logs the input with a given label and passes it through."""
    return RunnableLambda(lambda x: logger.info(f"Runnable '{label}' output: {x}") or x)


summarize_chain: Runnable = (
    ChatPromptTemplate.from_messages(
        [("system", "Summarize the following text concisely:"), ("user", "{topic}")]
    | llm
    | StrOutputParser()
    | log_runnable("Summary")
)

questions_chain: Runnable = (
    | llm
    | StrOutputParser()
    | log_runnable("Questions")
)

terms_chain: Runnable = (
    | llm
    | StrOutputParser()
    | log_runnable("Key Terms")
)
```

### How to Run

To run the script, use `uv run`:

```bash
uv run langchain-parallel.py
```

This will run the script with the default topic ("The history and future of space exploration").

#### Options

You can also provide a custom topic using the `--topic` flag:

```bash
uv run langchain-parallel.py --topic "The impact of AI on software development"
```

To see verbose output, including the output from each parallel chain, use the `--verbose` flag:

```bash
uv run langchain-parallel.py --topic "The impact of AI on software development" --verbose
```
