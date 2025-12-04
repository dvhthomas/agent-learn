# Agentic Patterns

Code samples from learning how to create and orchestrate AI agents from [Agentic Design Patterns](https://www.amazon.com/Agentic-Design-Patterns-Hands-Intelligent/dp/3032014018/).

This project contains the code samples from the book (modified by me and various coding agents!) with a key addition: a shared `common` library for standardized logging across all sub-projects.

## Project Structure

- **Numbered Folders (`1-prompt-chaining`, etc.):** Each folder is a standalone `uv` project corresponding to a chapter or pattern from the book.
- **`common/`:** A shared Python library that provides common utilities, primarily a sophisticated logging setup powered by the `rich` library.

## Getting Started

1.  **Install Prerequisites:**
    - Install Python 3.13+. (`asdf install python 3.13.5`)
    - Install `uv`. (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

2.  **Work on a Sub-Project:**
    - Navigate to a project directory: `cd <project_name>`
    - Install its dependencies: `uv sync`

3.  **Enable Shared Logging (Recommended):**
    - To use the shared logging library, link it to the project: `uv add ../common --editable`
    - This only needs to be done once per sub-project.

4.  **Run the Code:**
    - `uv run main.py` (or similar).
    - Use the `-v` or `-vv` flags to increase log verbosity.

## Common Logging Library

The `common` library provides standardized logging with colored output.
Add this to scripts by running `uv add ../common --editable` in the project directory.
The [template.py](template.py) script has a minimal setup implementation so from your project directory:

```sh
cp ../template.py your_script.py
```

### Usage

After setting it up (step 3 above), modify your main script to use the logging helpers. There are three main levels:

- `logger.notice()`: For essential user-facing messages. **Always visible by default.**
- `logger.info()`: For detailed diagnostic messages. Visible with `-v`.
- `logger.debug()`: For verbose debugging messages. Visible with `-vv`.
