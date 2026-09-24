from pathlib import Path
from openai import APIConnectionError, AuthenticationError, NotFoundError, OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_KEYS = {"", "your_openai_api_key_here", "your_api_key_here"}


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    knowledge_base_path: Path = Path("knowledge_base.txt")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_runtime(self) -> None:
        """Validate API key, model availability, and knowledge base file before running agents."""
        api_key = self.openai_api_key.strip()
        model = self.openai_model.strip()

        if api_key in PLACEHOLDER_KEYS:
            raise ValueError(
                "Missing or invalid OPENAI_API_KEY.\n"
                "Please set a valid OPENAI_API_KEY in your '.env' file."
            )

        if not model:
            raise ValueError(
                "Missing OPENAI_MODEL.\n"
                "Please set a valid OPENAI_MODEL (e.g., 'gpt-5-mini', 'gpt-5-nano', 'gpt-4o') in your '.env' file."
            )

        if not str(self.knowledge_base_path).strip() or not self.knowledge_base_path.exists() or not self.knowledge_base_path.is_file():
            raise FileNotFoundError(
                f"Knowledge base file not found: '{self.knowledge_base_path}'.\n"
                "Please ensure 'knowledge_base.txt' exists or update KNOWLEDGE_BASE_PATH in '.env'."
            )

        if not self.knowledge_base_path.read_text(encoding="utf-8").strip():
            raise ValueError(
                f"Knowledge base file '{self.knowledge_base_path}' is empty."
            )

        try:
            OpenAI(api_key=api_key).models.retrieve(model)
        except AuthenticationError as err:
            raise ValueError(
                "Invalid OPENAI_API_KEY.\n"
                "OpenAI rejected the API key. Please check OPENAI_API_KEY in your '.env' file."
            ) from err
        except NotFoundError as err:
            raise ValueError(
                f"Invalid OPENAI_MODEL: '{model}'.\n"
                "This model does not exist or your API key does not have access to it."
            ) from err
        except APIConnectionError as err:
            raise ValueError(
                "Could not connect to OpenAI API. Please check your network connection."
            ) from err


settings = Settings()
