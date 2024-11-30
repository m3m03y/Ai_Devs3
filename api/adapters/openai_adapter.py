"""Adapter for OpenAi Api"""

import os
from openai import OpenAI
from adapters.ai_interface import AiInterface
from conf.logger import LOG


class OpenAiAdapter(AiInterface):
    """Interface for connection with OpenAi API"""

    def __init__(self, api_key: str = None, base_url: str = None):
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        elif base_url:
            self.openai_client = OpenAI(base_url=base_url)

    def get_first_completions(
        self,
        model_name: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        top_p: float = 1,
    ) -> str:
        """Get first choice from Ai Assistant completions"""
        completions = self.openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        message = completions.choices[0].message
        LOG.debug("Response from Ai Assistant: %s.", message)
        content = message.content
        LOG.debug("Content of message from Ai Assistant: %s.", content)
        return content
