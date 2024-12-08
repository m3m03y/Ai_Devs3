"""Adapter for Groq Ai interface"""

import os
from groq import Groq, BadRequestError
from adapters.ai_interface import AiInterface
from conf.logger import LOG
from common.exceptions import AiAssistantException

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
groq_client = Groq(api_key=GROQ_API_KEY)


class GroqAdapter(AiInterface):
    """Interface for connection with Groq API"""

    def get_first_completions(
        self,
        model_name: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        top_p: float = 1,
    ) -> str:
        """Get first choice from Ai Assistant completions"""
        try:
            completions = groq_client.chat.completions.create(
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
        except BadRequestError as e:
            LOG.error(
                "Could not get completions for messages: %s. Error: %s.",
                messages,
                e.message,
            )
            raise AiAssistantException(e.status_code, e.message) from e

    def get_embeddings(self, model_name, data) -> list:
        result = groq_client.embeddings.create(input=data, model=model_name)
        LOG.debug("Embeddings result: %s.", result)
        return result.data

    def create_query_vector(self, query_input, model_name) -> list[float]:
        query_vector = (
            groq_client.embeddings.create(input=query_input, model=model_name)
            .data[0]
            .embedding
        )
        LOG.debug("Query vector for query: '%s': %s.", query_input, query_vector)
        return query_vector
