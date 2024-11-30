"""Common structure for interaction with AI interfaces"""

from abc import ABC, abstractmethod


class AiInterface(ABC):
    """Ai Assistant Interface definition"""

    @abstractmethod
    def get_first_completions(
        self,
        model_name: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        top_p: float = 1,
    ) -> str:
        """Get first choice from completions"""

    def build_image_content(self, text: str, image_url: str) -> list[dict]:
        """Build chat messages with image description and url"""
        return [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
