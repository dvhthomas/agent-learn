# AGENTS.md

## Development Environment Tips

- Each top level directory is a separate Python project created with the `uv` tool.
- Most scripts have a verbose flag where more `v`s increase the verbosity level. So use `-vv` for more verbose output.
- Use the `uv add` and `uv remove` commands to manage dependencies. Do not use `pip` or `poetry` to manage dependencies.
- Project scripts should be run with `uv run <script_name>`.

## Technical Choices

- For projects that include Google Agent Development Kit (ADK) `google-adk` in the pyproject.toml file, based your answers primarily on the [Google Agent Development Kit (ADK) documentation](https://google.github.io/adk-docs/).
- Strongly prefer explicit Python typing over duck typing.

## Documentation

- Keep the README.md in each top level directory up to date with a short description of each script.
- Use Mermaid diagrams in README.md files to illustrate the sequence of events in each script.
- Always put a new sentence on a new line in markdown documents so that changes to README.md files are easier to review in pull requests.
