import json
import requests
import os
from dotenv import load_dotenv
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

load_dotenv()

def search(query):
    try:
        url = "https://google.serper.dev/search"
        serper_token = os.getenv("SERPER_API_KEY")
        payload = json.dumps({
            "q": query,
            "gl": "vn",
            "hl": "vi"
        })
        headers = {
            'X-API-KEY': serper_token,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code != 200:
            raise InternalServerError(str(response.message))
        return response.json()
    except Exception as e:
        print("SERP: Error occur", str(e)) 
        raise InternalServerError("error while search information")