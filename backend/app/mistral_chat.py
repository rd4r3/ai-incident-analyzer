from typing import Any, Dict, List, Optional, TypedDict
import requests

from langchain.chat_models.base import BaseChatModel
from langchain.schema import AIMessage, BaseMessage, ChatGeneration, ChatResult, HumanMessage
from .logging_config import setup_logging

# Set up logging
logger = setup_logging(__name__)

class ApiResponse(TypedDict):
    """Type definition for the API response structure."""
    choices: List[Dict[str, Any]]

class ChatMistral(BaseChatModel):
    """Chat model implementation for Mistral AI API.

    Args:
        api_key: API key for authentication
        model_name: Name of the model to use (default: "open-mistral-7b")
        temperature: Temperature for response generation (default: 0.1)
        api_endpoint: API endpoint URL (default: Mistral AI API)
    """
    api_key: str
    model_name: str = "open-mistral-7b"
    temperature: float = 0.1
    api_endpoint: str = "https://api.mistral.ai/v1/chat/completions"

    @property
    def _llm_type(self) -> str:
        """Return the type of language model."""
        return "mistral"

    def _prepare_payload(self, messages: List[HumanMessage]) -> Dict[str, Any]:
        """Prepare the payload for the API request."""
        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": m.content} for m in messages],
            "temperature": self.temperature,
        }

    def _make_api_request(self, payload: Dict[str, Any]) -> ApiResponse:
        """Make the API request and handle the response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            logger.debug("Making API request to Mistral AI")
            resp = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=30  # Add timeout for better error handling
            )
            resp.raise_for_status()
            logger.debug("API request successful")
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        finally:
            # Ensure resources are cleaned up
            resp.close()

    def _call(self, messages: List[HumanMessage], **kwargs: Any) -> Dict[str, Any]:
        """Call the Mistral AI API with the given messages."""
        payload = self._prepare_payload(messages)
        return self._make_api_request(payload)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> ChatResult:
        """Generate chat responses from the model.

        Args:
            messages: List of input messages
            stop: Optional list of stop words
            **kwargs: Additional keyword arguments

        Returns:
            ChatResult containing the generated responses
        """
        try:
            # 1) Filter only the user messages
            user_msgs = [m for m in messages if isinstance(m, HumanMessage)]

            # 2) Get API response
            api_resp = self._call(user_msgs, stop=stop)

            # 3) Build a flat list of ChatGeneration
            gens = [
                ChatGeneration(
                    message=AIMessage(content=choice["message"]["content"])
                )
                for choice in api_resp.get("choices", [])
            ]

            # 4) Return with a 1D generations list
            return ChatResult(
                generations=gens,
                llm_output=api_resp,
            )
        finally:
            # Clean up any resources
            pass
