"""Custom Exceptions"""


class AiDevsApiException(Exception):
    """Exceptions from AiDevs Api"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class AiAssistantException(Exception):
    """Exceptions from communication with Ai assistants"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
