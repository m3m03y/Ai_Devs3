"""Common images actions"""

import base64


def encode_image(image: str | bytes) -> str:
    """Encode image in base64"""
    return base64.b64encode(image).decode("utf-8")


def image_url_from_base64(image: str) -> dict:
    """Build image url with base64 encoding"""
    return f"data:image/jpeg;base64,{image}"
