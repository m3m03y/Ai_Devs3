"""Common tools"""

import json
import copy

def pretty_json(text: str):
    """
    Returns formatted json message
    """
    print_text = copy.deepcopy(text)
    if 'apikey' in print_text:
        print_text['apikey']='<hidden>'
    return json.dumps(print_text, sort_keys=True, indent=4)
