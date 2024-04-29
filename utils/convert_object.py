import json
import re

def convertObj(text):
    match = re.search(r'\{.*\}', text)
    if match:
        json_str = match.group(0)
        # Convert the JSON string to a Python dictionary
        original_data = json.loads(json_str)

        # Create a new dictionary in the desired format
        formatted_data = {
            'content': None,
            'role': 'assistant',
            'function_call': {
                'name': original_data['function']['name'],
                'arguments': json.dumps(original_data['parameters'])
            }
        }
        return formatted_data
    else:
        return text
