# Marketing Agent Project

This project is a marketing agent built with Google's Agent Development Kit (ADK) framework. It assists with marketing tasks using agents and tools.

## Features

- **ADK Integration:** Uses the `google-adk` framework for agent capabilities.
- **Modular Structure:** Organized into a `MarketingAgent` package with specialized assistants for different marketing functions (e.g., generation, editing).
- **Configuration:** Settings are managed through `config.py`.
- **Extensibility:** Structured for easy addition of new tools and assistant capabilities.

## Requirements

- Python 3.12+
- [Poetry](https://python-poetry.org/) for dependency management

## Installation

1.  **Clone the repository (if you haven't already):**
    ```sh
    # Ensure you are in the root of the ai-ml-agentic-rock project
    git clone <repository-url>
    cd ai-ml-agentic-rock
    ```

2.  **Navigate to the project directory:**
    ```sh
    cd Demos/marketing
    ```

3.  **Install dependencies using Poetry:**
    ```sh
    poetry install
    ```

4.  **Set up environment variables:**
    Create a `.env` file from the example. You may need to update the variables in `.env`.
    ```sh
    cp .env.example .env
    ```

## Usage

1.  **Navigate to the project directory (if you are not already there):**
    ```sh
    cd Demos/marketing
    ```

2.  **Start the application using the ADK web server:**
    ```sh
    poetry run adk web
    ```
    This starts a local web server to interact with the agent.

## Project Structure

```plaintext
Demos/marketing/
├── MarketingAgent/         # Main package for the marketing agent
│   ├── __init__.py
│   ├── agent.py            # Core agent logic
│   ├── config.py           # Configuration settings
│   ├── tools.py            # Tools available to the agent
│   ├── assistants/         # Sub-agents for specialized tasks
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── editing/        # Assistant for editing tasks
│   │   └── generation/     # Assistant for generation tasks
│   └── templates/          # Prompt templates
├── pyproject.toml          # Project metadata and dependencies
├── poetry.lock             # Exact versions of dependencies
└── README.md               # This file
```

## Agent Overview

The `MarketingAgent` uses sub-agents (assistants) and tools for tasks like:

-   Content generation
-   Content editing and refinement
-   (Add other specific tasks the agent can perform)

Agent behavior is defined by instructions and configurations in its package.

## Limitations

- **Image Editing Access:** The image editing functionality, which utilizes the `imagen-3.0-capability-001` model, currently requires users to have trusted tester access to Google's Imagen 3.0 capabilities.

## Future Improvements

- **Prompt Refinement:** The prompts used by the agent for various tasks (generation, editing, etc.) can be further refined to improve the quality and relevance of the output.
- **Error Handling:** Enhance error handling and provide more informative feedback to the user.
- **Tool Expansion:** Add more specialized tools to broaden the agent's marketing capabilities.