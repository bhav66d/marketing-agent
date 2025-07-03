from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic_settings import BaseSettings, SettingsConfigDict
from google import genai
from pydantic import model_validator


@lru_cache()
class Config(BaseSettings):
    """Base settings class."""

    # Google Cloud settings
    GOOGLE_GENAI_USE_VERTEXAI: bool = True
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GEMINI_API_KEY: str | None = None
    TEMPLATES_FOLDER: str = "templates"

    # Application settings
    HOST_URL: str = "0.0.0.0"
    DEVELOPMENT: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_settings(self):
        """Validate settings after initialization.

        Raises:
            ValueError: If GOOGLE_GENAI_USE_VERTEXAI is False and GEMINI_API_KEY is not provided.
        """
        if not self.GOOGLE_GENAI_USE_VERTEXAI and not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY must be provided when GOOGLE_GENAI_USE_VERTEXAI is False"
            )
        return self


config = Config()


@lru_cache()
def get_genai_client() -> genai.Client:
    """Get a configured GenAI client instance.

    Returns:
        genai.Client: A configured client instance.
    """
    if config.GOOGLE_GENAI_USE_VERTEXAI:
        client = genai.Client(
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.GOOGLE_CLOUD_LOCATION,
        )

    # If not using Vertex AI, use the API key for authentication
    else:
        client = genai.Client(api_key=config.GEMINI_API_KEY)

    return client


genai_client = get_genai_client()


@lru_cache()
def create_jinja2_env(templates_folder: str, enable_async: bool = True) -> Environment:
    """Creates a Jinja2 environment.

    Args:
        templates_folder (str): The folder containing the Jinja2 templates.
        enable_async (bool): Whether to enable async support. Defaults to True.

    Returns:
        Environment: A Jinja2 environment instance.
    """
    root_directory = Path(__file__).parent
    templates_directory = root_directory / templates_folder

    return Environment(
        loader=FileSystemLoader(templates_directory), enable_async=enable_async
    )


# Create a global Jinja2 environment instance
jinja2_env = create_jinja2_env(config.TEMPLATES_FOLDER, enable_async=False)


class GeminiModelOptions(StrEnum):
    """Enum for Gemini model options.

    This enum provides a list of available Gemini models for use in the application.
    The models are categorized into different versions, including preview and experimental models.

    See Also:
        Google AI Studio Model Documentation:
        https://ai.google.dev/models/gemini
    """

    # Official models
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_2_0_FLASH = "gemini-2.0-flash-001"
    IMAGEN_3_0_GENERATE = "imagen-3.0-generate-002"
    IMAGEN_3_0_EDIT = "imagen-3.0-capability-001"  # Requires trusted tester access

    # Preview/Experimental models
    GEMINI_2_5_FLASH = "gemini-2.5-flash-preview-04-17"
    GEMINI_2_5_PRO = "gemini-2.5-pro-preview-05-06"

    @classmethod
    def default(cls) -> "GeminiModelOptions":
        """Get the default model option.

        Returns:
            GeminiModelOptions: The default model option. This is set to `GEMINI_2_0_FLASH`."""

        return cls.GEMINI_2_0_FLASH

    @classmethod
    def from_string(cls, value: str) -> "GeminiModelOptions":
        """Convert a string to the corresponding enum member.

        Args:
            value (str): The string representation of the model.

        Returns:
            GeminiModelOptions: The corresponding enum member.
        """
        try:
            return cls(value)

        except ValueError:
            available = ", ".join([f"'{item.value}'" for item in cls])

            raise ValueError(
                f"'{value}' is not a valid Gemini model. Available models: {available}"
            )
