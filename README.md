# Agentic Patterns

Code samples from learning how to create and orchestrate AI agents from [Agentic Design Patterns](https://www.amazon.com/Agentic-Design-Patterns-Hands-Intelligent/dp/3032014018/).

## Setup

1. Install Python. `asdf install python 3.13.5`
1. Install uv. `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Work on a project

Each folder is it's own isolated `uv` project relating to a single chapter or pattern.

1. From the root directory, `cd <project_name>` then `uv sync` to install the project dependencies.
2. `uv run main.py` (or similar) to run the project. Some scripts have `--verbose` flags to dump more LLM internals.

I've used `logging` more that `print` statements but other than that there are very few differences between my code and what's in the book.
I did use an LLM to help write the `README.md` in each folder so that I understand how things are working if they were unclear to me. Again, your mileage might vary.


## Optional Tooling

Optionally, install [ruff](https://astral.sh/blog/the-ruff-formatter) globally and configure your editor to lint on the fly (red squiggly lines) and to format on save.

```sh
uv tool install ruff
```

For example, Zed will use `ruff` to lint and format with this configuration:

```json
  "languages": {
    "Python": {
      "language_servers": ["ruff"],
      "formatter": {
        "external": {
          "command": "ruff",
          "arguments": ["format", "--stdin-filename", "{buffer_path}", "-"]
        }
      },
      "format_on_save": "on"
    }
  },
  "lsp": {
    "ruff": {
      "binary": {
        "path": "ruff",
        "arguments": ["server"]
      }
    }
  }
```
