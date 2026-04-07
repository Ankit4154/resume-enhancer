from abc import ABC, abstractmethod
import json
import os
import requests
from config import GLOBAL_API_KEY, BASE_URL, ENDPOINT, MODEL


class AIModelProvider(ABC):
    @abstractmethod
    async def get_completion(self, prompt: str, model: str = MODEL, base_url: str = BASE_URL) -> str:
        ...
        
class GlobalAIProvider(AIModelProvider):
    async def get_completion(self, prompt: str, model: str = MODEL, base_url: str = BASE_URL):
        url = f"{base_url}{ENDPOINT}"
        payload = {
            "model": f"{model}",
            "messages": [
                {
                 "role": "user", 
                 "content": f"{prompt}" 
                },
            ]
        }
        response = requests.post(url, json=payload, stream=False)
        out = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                out += data.get("message", {}).get("content", "")
        return json.loads(out)