from abc import ABC, abstractmethod
import json
import os
import requests
from config import BASE_URL, ENDPOINT, MODEL


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
        response = requests.post(url, json=payload, stream=True)
        if response.status_code != 200:
            raise ValueError(
                f"API request failed with status {response.status_code}: {response.reason}. Response: {response.text}"
            )
        out = ""
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                # Skip non-JSON lines (like thinking text or markdown)
                continue

            if isinstance(data, dict):
                if isinstance(data.get("message"), dict):
                    out += data["message"].get("content", "")
                elif isinstance(data.get("content"), str):
                    out += data["content"]

        if not out:
            try:
                data = response.json()
                if isinstance(data, dict):
                    if isinstance(data.get("message"), dict):
                        out = data["message"].get("content", "")
                    elif isinstance(data.get("content"), str):
                        out = data["content"]
                    else:
                        out = json.dumps(data)
            except ValueError:
                out = response.text
        
        out = out.strip()
        
        # Extract JSON object from content if it's embedded in text/markdown
        if out and not out.startswith('{'):
            start_idx = out.find('{')
            if start_idx != -1:
                end_idx = out.rfind('}')
                if end_idx != -1:
                    out = out[start_idx:end_idx+1]
        
        return out