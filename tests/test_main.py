"""Main function tests"""

import json
import os
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.utils import pretty_json

client = TestClient(app)


@pytest.mark.parametrize(
    "expected_description",
    [
        "abc\ncdf\n",
        # [1, 2, 3, 4],
        # {"test": 1, "other-value": 2},
    ],
)
def test_get_description(mocker, expected_description):
    """
    Given specific task url, the api should return
    the response without alterations
    """
    mock_response = mocker.Mock()
    mock_response.text = expected_description
    mocker.patch("requests.get", return_value=mock_response)
    task_json = json.dumps({"task_url": "test-path"})
    result = client.post("/get-task", content=task_json, timeout=30)
    assert result.text == expected_description


def test_send_answer():
    """
    Given test task solution and urls should respond
    with 200 ok and correct message
    """
    task_name = "POLIGON"
    task_url = os.environ["TEST_TASK_URL"]
    answer_url = os.environ["TEST_ANSWER_URL"]

    task_json = json.dumps({"task_url": task_url})
    task = client.post("/get-task", content=task_json, timeout=30)
    answer_list = task.text.splitlines()
    answer_json = json.dumps(
        {"task_id": task_name, "answer_url": answer_url, "answer_content": answer_list}
    )
    response = client.post("/send-answer", content=answer_json, timeout=30)
    expected_success_message = pretty_json(
        {"code": 0, "message": "Super. Wszystko OK!"}
    )
    expected_response_content = (
        f"Answer send successfully, response status code=200\n"
        f"Message:\n"
        f"{expected_success_message}"
    )
    assert response.text == expected_response_content
