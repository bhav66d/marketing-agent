from typing import Dict, Any, Optional
from enum import Enum

from google.adk.tools import ToolContext
from google.genai import types
from google.genai.types import RawReferenceImage, MaskReferenceImage
from MarketingAgent.config import genai_client, GeminiModelOptions
from MarketingAgent.assistants.common import save_image_to_cache


class MaskMode(str, Enum):
    """Enum for mask modes in image editing."""

    BACKGROUND = "MASK_MODE_BACKGROUND"
    FOREGROUND = "MASK_MODE_FOREGROUND"
    NONE = "MASK_MODE_UNSPECIFIED"


class EditMode(str, Enum):
    """Enum for edit modes in image editing."""

    INPAINT = "EDIT_MODE_INPAINT_INSERTION"
    STYLE = "EDIT_MODE_STYLE_TRANSFER"
    BASIC = "EDIT_MODE_UNSPECIFIED"


def _edit_image_with_imagen(
    image_bytes: bytes,
    prompt: str,
) -> Optional[bytes]:
    """Edit an image using Imagen 3.0 with fixed background masking and inpainting.

    Args:
        image_bytes: Raw bytes of the source image to edit.
        prompt: The text prompt describing the desired edit.

    Returns:
        bytes: The raw image bytes of the edited image, or None if editing failed.
    """
    try:
        # Create a raw reference image from the source image bytes
        raw_image = types.Image(image_bytes=image_bytes)

        raw_ref_image = RawReferenceImage(
            reference_id=1,
            reference_image=raw_image,
        )

        # Create mask reference with fixed BACKGROUND mode
        mask_ref_image = MaskReferenceImage(
            reference_id=2,
            config=types.MaskReferenceConfig(
                mask_mode="MASK_MODE_FOREGROUND",
                mask_dilation=0.1,
            ),
        )

        # Call the API to edit the image with fixed INPAINT mode
        response = genai_client.models.edit_image(
            model=GeminiModelOptions.IMAGEN_3_0_EDIT,
            prompt=prompt,
            reference_images=[raw_ref_image, mask_ref_image],
            config=types.EditImageConfig(
                edit_mode="EDIT_MODE_INPAINT_INSERTION",
                number_of_images=1,
                include_rai_reason=True,
                output_mime_type="image/png",
            ),
        )

        # Return the edited image bytes if available
        if response.generated_images and len(response.generated_images) > 0:
            return response.generated_images[0].image.image_bytes

        return None

    except Exception as e:
        print(f"Error editing image with Imagen: {e}")
        return None


def _free_edit_image_with_imagen(
    image_bytes: bytes,
    prompt: str,
) -> Optional[bytes]:
    """Edit an image using Imagen 3.0 without applying a mask.

    This function performs a free-form edit on the entire image based on
    the provided prompt, without specifying areas to edit via masks.

    Args:
        image_bytes: Raw bytes of the source image to edit.
        prompt: The text prompt describing the desired edit.

    Returns:
        bytes: The raw image bytes of the edited image, or None if editing failed.
    """
    try:
        # Create a raw reference image from the source image bytes
        raw_image = types.Image(image_bytes=image_bytes)

        raw_ref_image = RawReferenceImage(
            reference_id=1,
            reference_image=raw_image,
        )

        # Call the API to edit the image with DEFAULT mode (no mask required)
        response = genai_client.models.edit_image(
            model=GeminiModelOptions.IMAGEN_3_0_EDIT,
            prompt=prompt,
            reference_images=[raw_ref_image],  # Only the raw image, no mask
            config=types.EditImageConfig(
                edit_mode="EDIT_MODE_DEFAULT",
                number_of_images=1,
                include_rai_reason=True,
                safety_filter_level="BLOCK_ONLY_HIGH",
                person_generation="DONT_ALLOW",  # Safety settings do not allow person generation
                output_mime_type="image/png",
            ),
        )

        # Return the edited image bytes if available
        if response.generated_images and len(response.generated_images) > 0:
            return response.generated_images[0].image.image_bytes

        return None

    except Exception as e:
        print(f"Error with free-form image editing: {e}")
        return None


async def edit_image(
    image_filename: str,
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Tool to edit an existing image based on a text prompt.

    Args:
        image_filename: The filename of the image to edit.
        prompt: The text prompt describing the desired edit.
        tool_context: The tool execution context with artifact service access.

    Returns:
        A dictionary with artifact information including filename and version.
    """
    try:
        # For testing, let's use a placeholder image instead of trying to get it from artifacts
        with open(f".cache/{image_filename}", "rb") as f:
            image_bytes = f.read()

        # Include context state for debugging
        context_state = {}
        if hasattr(tool_context, "state") and hasattr(tool_context.state, "to_dict"):
            context_state = tool_context.state.to_dict()

        # Edit the image - simplified with fixed parameters
        edited_image_bytes = _edit_image_with_imagen(
            image_bytes=image_bytes,
            prompt=prompt,
        )

        if not edited_image_bytes:
            return {
                "success": False,
                "error": "Image editing failed",
                "context_state": context_state,
            }

        # Create a Part object with the edited image data
        edited_image_artifact = types.Part.from_bytes(
            data=edited_image_bytes, mime_type="image/png"
        )

        # Generate a filename for the edited image
        sanitized_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
        edit_filename = f"edited_image_{sanitized_prompt}.png"

        saved_filepath = save_image_to_cache(
            image_bytes=edited_image_bytes, filename=edit_filename
        )
        if not saved_filepath:
            print(f"Error saving image to cache: {edit_filename}")
            return {
                "prompt": prompt,
                "success": False,
                "error": "Failed to save image to cache",
            }

        # Save the edited image as a new artifact
        version = await tool_context.save_artifact(
            filename=edit_filename, artifact=edited_image_artifact
        )

        # Return metadata about the saved artifact
        return {
            "requested_image": image_filename,
            "prompt": prompt,
            "mask_mode": "MASK_MODE_BACKGROUND",
            "edit_mode": "EDIT_MODE_INPAINT_INSERTION",
            "artifact_filename": edit_filename,
            "artifact_version": version,
            "mime_type": "image/png",
            "context_state": context_state,
            "success": True,
        }

    except ValueError as e:
        print(f"Error with artifact service: {e}")
        return {"success": False, "error": f"Artifact service error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error during image editing: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


async def free_edit_image(
    image_filename: str,
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Tool to perform a free-form edit on an image without applying masks.

    This tool applies edits to the entire image based on the prompt, without
    specifically masking regions. Useful for style transfers and global changes.

    Args:
        image_filename: The filename of the image to edit.
        prompt: The text prompt describing the desired edit.
        tool_context: The tool execution context with artifact service access.

    Returns:
        A dictionary with artifact information including filename and version.
    """
    try:
        # For testing, load the image from cache
        with open(f".cache/{image_filename}", "rb") as f:
            image_bytes = f.read()

        # Include context state for debugging
        context_state = {}
        if hasattr(tool_context, "state") and hasattr(tool_context.state, "to_dict"):
            context_state = tool_context.state.to_dict()

        # Edit the image without masking
        edited_image_bytes = _free_edit_image_with_imagen(
            image_bytes=image_bytes,
            prompt=prompt,
        )

        if not edited_image_bytes:
            return {
                "success": False,
                "error": "Free-form image editing failed",
                "context_state": context_state,
            }

        # Create a Part object with the edited image data
        edited_image_artifact = types.Part.from_bytes(
            data=edited_image_bytes, mime_type="image/png"
        )

        # Generate a filename for the edited image
        sanitized_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
        edit_filename = f"free_edit_{sanitized_prompt}.png"

        # Save the edited image to cache
        saved_filepath = save_image_to_cache(
            image_bytes=edited_image_bytes, filename=edit_filename
        )
        if not saved_filepath:
            print(f"Error saving image to cache: {edit_filename}")
            return {
                "prompt": prompt,
                "success": False,
                "error": "Failed to save image to cache",
            }

        # Save as artifact
        version = await tool_context.save_artifact(
            filename=edit_filename, artifact=edited_image_artifact
        )

        # Return metadata
        return {
            "requested_image": image_filename,
            "prompt": prompt,
            "edit_mode": "EDIT_MODE_DEFAULT",
            "artifact_filename": edit_filename,
            "artifact_version": version,
            "mime_type": "image/png",
            "context_state": context_state,
            "success": True,
        }

    except ValueError as e:
        print(f"Error with artifact service: {e}")
        return {"success": False, "error": f"Artifact service error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error during free-form editing: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
