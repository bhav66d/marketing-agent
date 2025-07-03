from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from MarketingAgent.assistants.editing.agent import image_editing_agent
from MarketingAgent.assistants.generation.agent import image_generation_agent


async def call_image_generation_agent(
    tool_context: ToolContext,
    prompt: str,
):
    """Tool to call the image generation agent.

    This tool delegates image generation to a specialized agent that can create
    images based on text prompts.

    Args:
        tool_context: The tool execution context with artifact service access.
        prompt: The text prompt for image generation.


    Returns:
        The output from the image generation agent, including artifact metadata.
    """
    agent_tool = AgentTool(agent=image_generation_agent)

    generation_output = await agent_tool.run_async(
        args={"request": prompt}, tool_context=tool_context
    )

    # Store the output in the context state for reference
    if hasattr(tool_context, "state"):
        tool_context.state["image_generation_output"] = generation_output

    return generation_output


async def call_image_editing_agent(
    tool_context: ToolContext,
    image_filename: str,
    prompt: str,
):
    """Tool to call the image editing agent.

    This tool delegates image editing to a specialized agent that can modify
    existing images based on text prompts.

    Args:
        tool_context: The tool execution context with artifact service access.
        image_filename: The filename of the image to edit.
        prompt: The text prompt describing the desired edit.

    Returns:
        The output from the image editing agent, including artifact metadata.
    """
    agent_tool = AgentTool(agent=image_editing_agent)

    # Format a request string with all the parameters
    request = f"Edit image '{image_filename}' with the following prompt: {prompt}."

    editing_output = await agent_tool.run_async(
        args={"request": request}, tool_context=tool_context
    )

    # Store the output in the context state for reference
    if hasattr(tool_context, "state"):
        tool_context.state["image_editing_output"] = editing_output

    return editing_output
