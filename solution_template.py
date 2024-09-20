"""AiDevs task solution template"""
import json
import os
import copy
import requests

TASK='POLIGON'
TASK_URL='https://poligon.aidevs.pl/dane.txt'
ANSWER_URL='https://poligon.aidevs.pl/verify'
API_KEY=os.environ['API_KEY']

def pretty_json(text: str):
    """
    Returns formatted json message
    """
    print_text = copy.deepcopy(text)
    if 'apikey' in print_text:
        print_text['apikey']='<hidden>'
    print(json.dumps(print_text, sort_keys=True, indent=4))

def solve_task(task_text: str):
    """
    Valid answer format:
    {
        "task": "1234",
        "apikey": "Twój klucz API",
        "answer": [0,1,2,3,4]
    }
    """

    # Base solution
    answer_list = task_text.splitlines()
    answer = {"task": TASK, "apikey": API_KEY, "answer": answer_list}
    print(pretty_json(answer))

    return json.dumps(answer)

if __name__=="__main__":
    task = requests.get(TASK_URL, timeout=30)
    result = requests.post(ANSWER_URL, data=solve_task(task.text), timeout=30)
    print(f'Result status code = {result.status_code}\nResult body:\n{result.text}')
