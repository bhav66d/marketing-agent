# Use an official Python runtime and specify a linux/amd64 platform
FROM --platform=linux/amd64 python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Install Poetry via pip (which handles architecture correctly)
RUN pip install poetry==2.1.3

# Set the working directory in the container
WORKDIR /marketing

# Copy the dependency files and README
COPY pyproject.toml poetry.lock* README.md ./

# Copy MarketingAgent to the working directory
COPY MarketingAgent/ ./MarketingAgent/

# Install project dependencies
RUN poetry install

# Expose the port the app runs on
EXPOSE 8080

# Command to run ADK web
CMD ["poetry", "run", "adk", "web", "--port", "8080"]
