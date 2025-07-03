from typing import Any
from typing import Dict
from typing import Optional

from google.adk.tools import ToolContext
from google.genai import types

from MarketingAgent.config import GeminiModelOptions
from MarketingAgent.config import genai_client
from MarketingAgent.assistants.common import save_image_to_cache

# CLIENT VISUAL IDENTITY CONFIGURATION
CLIENT_VISUAL_CONFIG = {
    "brand_colors": {
        "primary": "{PRIMARY_COLOR_HEX}",
        "primary_name": "{PRIMARY_COLOR_NAME}",
        "secondary": "{SECONDARY_COLOR_HEX}", 
        "secondary_name": "{SECONDARY_COLOR_NAME}",
        "accent": "{ACCENT_COLOR_HEX}",
        "accent_name": "{ACCENT_COLOR_NAME}"
    },
    "logo_guidelines": {
        "style": "{LOGO_STYLE_DESCRIPTION}",
        "colors": "{LOGO_COLOR_SCHEME}",
        "elements": "{LOGO_KEY_ELEMENTS}",
        "restrictions": "{LOGO_USAGE_RESTRICTIONS}"
    },
    "imagery_style": {
        "composition": "{PREFERRED_COMPOSITION_STYLE}",
        "subject_matter": "{PREFERRED_SUBJECTS}",
        "setting": "{PREFERRED_SETTINGS}",
        "mood": "{PREFERRED_MOOD}",
        "style": "{VISUAL_STYLE_PREFERENCE}",
        "avoid": "{IMAGERY_TO_AVOID}"
    },
    "industry_focus": "{CLIENT_INDUSTRY}",
    "brand_personality": "{BRAND_PERSONALITY}"
}

GUIDELINES = f"""
<visual_identity>
<brand_colors>
Primary Colors:
- {CLIENT_VISUAL_CONFIG['brand_colors']['primary_name']}: {CLIENT_VISUAL_CONFIG['brand_colors']['primary']} - {CLIENT_VISUAL_CONFIG['brand_personality']}
- {CLIENT_VISUAL_CONFIG['brand_colors']['secondary_name']}: {CLIENT_VISUAL_CONFIG['brand_colors']['secondary']} - {CLIENT_VISUAL_CONFIG['brand_colors']['secondary_name']} represents innovation and trust
- {CLIENT_VISUAL_CONFIG['brand_colors']['accent_name']}: {CLIENT_VISUAL_CONFIG['brand_colors']['accent']} - Used for highlights and accents

Always use these exact hex codes. {CLIENT_VISUAL_CONFIG['brand_colors']['primary_name']} should dominate visual elements.
</brand_colors>

<logo_guidelines>
- {CLIENT_VISUAL_CONFIG['logo_guidelines']['style']}
- {CLIENT_VISUAL_CONFIG['logo_guidelines']['colors']}
- {CLIENT_VISUAL_CONFIG['logo_guidelines']['elements']}
- {CLIENT_VISUAL_CONFIG['logo_guidelines']['restrictions']}
- Never alter proportions, colors, or orientation
- Maintain clear space around logo
</logo_guidelines>

<imagery_style>
- {CLIENT_VISUAL_CONFIG['imagery_style']['composition']}
- {CLIENT_VISUAL_CONFIG['imagery_style']['subject_matter']}
- {CLIENT_VISUAL_CONFIG['imagery_style']['setting']}
- {CLIENT_VISUAL_CONFIG['imagery_style']['mood']}
- {CLIENT_VISUAL_CONFIG['imagery_style']['style']}
- Incorporate brand colors naturally in backgrounds and settings
- Avoid {CLIENT_VISUAL_CONFIG['imagery_style']['avoid']}
- Hero images should showcase products and reinforce campaign themes
- Focus on {CLIENT_VISUAL_CONFIG['industry_focus']} industry context and scenarios
</imagery_style>
</visual_identity>

<channel_specific>
<website>
Professional, informative, solution-focused. Balance technical accuracy with accessibility.
</website>

<social_media>
Visual how-tos, team stories, {CLIENT_VISUAL_CONFIG['industry_focus']} lifestyle content. Keep approachable and community-focused.
</social_media>

<customer_service>
Patient and helpful. Focus on problem-solving and building customer confidence. Always go above and beyond.
</customer_service>
</channel_specific>
"""

INSTRUCTIONS = """
<who_are_you>You are a professional marketing specialist and Prompt Engineer for {CLIENT_NAME}.</who_are_you>
<tasks>
  <task>Review the content request the user requested.</task>
  <task>Review the brand guidelines, including the brand voice, tone, and visual identity.</task>
  <task>Write a detailed prompt that meets the user's request and adheres to the brand guidelines.</task>
</tasks>
<avoid>Adding texts, logos, or watermarks to the image.</avoid>
<avoid>Adding any other elements that are not part of the brand guidelines.</avoid>
<avoid>Adding the company name or any other brand name to the image.</avoid>
<response_output>A single paragraph of text with the enhanced prompt.</response_output>
""".format(CLIENT_NAME="{CLIENT_NAME}")


def _enhanche_prompt(prompt: str) -> str:
    """Enhance the prompt for better image generation."""
    user_request = f"<user_request>{prompt}</user_request>"
    brand_guidelines = f"<brand_guidelines>{GUIDELINES}</brand_guidelines>"
    response = genai_client.models.generate_content(
        model=GeminiModelOptions.GEMINI_2_0_FLASH,
        contents=[INSTRUCTIONS, brand_guidelines, user_request],
    )

    if not response or not response.text:
        return prompt

    return response.text


def _generate_image_with_imagen(
    prompt: str, number_of_images: int = 2, aspect_ratio: str = "1:1"
) -> Optional[bytes]:
    """Generate images using Imagen 3.0 and return the first image's bytes.

    Args:
        prompt: The text prompt for image generation.
        number_of_images: Number of images to generate (defaults to 2).
        aspect_ratio: The aspect ratio of the generated images (defaults to "1:1").

    Returns:
        bytes: The raw image bytes of the first generated image, or None if generation failed.
    """
    prompt = _enhanche_prompt(prompt)
    try:
        response = genai_client.models.generate_images(
            model=GeminiModelOptions.IMAGEN_3_0_GENERATE,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=number_of_images,
                aspect_ratio=aspect_ratio,  # Square image
                enhance_prompt=True,
            ),
        )

        # Return the first image's bytes if images were generated
        if response.generated_images and len(response.generated_images) > 0:
            return response.generated_images[0].image.image_bytes

        return None

    except Exception as e:
        print(f"Error generating image with Imagen: {e}")
        return None


async def generate_image(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Tool to generate an image based on a text prompt and save it as an artifact.

    This function generates a real image using Imagen 3.0, saves it as an artifact
    using the provided context, and returns metadata about the saved artifact.

    Args:
        prompt: The text prompt for image generation.
        tool_context: The tool execution context with artifact service access.

    Returns:
        A dictionary with artifact information including filename and version.
    """
    # Generate the image using Imagen
    image_bytes = _generate_image_with_imagen(prompt)

    # Create a Part object with the image data and MIME type
    image_artifact = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

    # Generate a filename based on the prompt
    sanitized_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
    filename = f"generated_image_{sanitized_prompt}.png"

    saved_filepath = save_image_to_cache(image_bytes=image_bytes, filename=filename)
    if not saved_filepath:
        print(f"Error saving image to cache: {filename}")
        return {
            "prompt": prompt,
            "success": False,
            "error": "Failed to save image to cache",
        }

    try:
        # Save the artifact and get the version number
        version = await tool_context.save_artifact(
            filename=filename, artifact=image_artifact
        )

        # Return metadata about the saved artifact
        return {
            "prompt": prompt,
            "artifact_filename": filename,
            "artifact_version": version,
            "mime_type": "image/png",
            "success": True,
        }
    except ValueError as e:
        # Handle case where artifact service is not configured
        print(f"Error saving artifact: {e}. Is ArtifactService configured?")
        return {
            "prompt": prompt,
            "success": False,
            "error": "Artifact service not configured",
        }
    except Exception as e:
        # Handle other potential errors
        print(f"Unexpected error during artifact save: {e}")
        return {
            "prompt": prompt,
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }