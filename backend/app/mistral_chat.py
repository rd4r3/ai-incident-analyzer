from typing import Any, List, Optional
import requests

from langchain.chat_models.base import BaseChatModel
from langchain.schema import AIMessage, BaseMessage, ChatGeneration, ChatResult, HumanMessage

class ChatMistral(BaseChatModel):
    api_key: str
    model_name: str = "open-mistral-7b"
    temperature: float = 0.1

    @property
    def _llm_type(self) -> str:
        return "mistral"

    def _call(self, messages: List[HumanMessage], **kwargs: Any) -> dict:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": m.content} for m in messages],
            "temperature": self.temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> ChatResult:
        # 1) Filter only the user messages
        user_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        api_resp = self._call(user_msgs, stop=stop)

        # 2) Build a flat list of ChatGeneration
        gens: List[ChatGeneration] = []
        for choice in api_resp.get("choices", []):
            ai_message = AIMessage(content=choice["message"]["content"])
            gens.append(ChatGeneration(message=ai_message))

        # 3) Return with a 1D generations list
        return ChatResult(
            generations=gens,
            llm_output=api_resp,
        )
