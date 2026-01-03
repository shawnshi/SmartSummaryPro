import requests
import json
import time
from .quota import QuotaManager
from .config import prefs

class APIManager:
    def __init__(self):
        self.quota_mgr = QuotaManager()

    def get_ordered_models(self):
        """
        Returns list of API configs sorted by user priority (if we had a priority field).
        For now, just return the list as is (assuming user ordered them in UI).
        """
        return prefs.get('api_configs', [])

    def generate_summary(self, prompt):
        """
        Try models in order until one succeeds.
        """
        models = self.get_ordered_models()
        if not models:
            raise Exception("No API models configured. Please check Settings.")

        errors = []

        for model in models:
            model_id = model.get('id')
            name = model.get('name')
            
            # 1. Check Quota
            if not self.quota_mgr.check_quota(model_id):
                print(f"Skipping {name}: Quota exceeded.")
                continue

            # 2. Try Execution
            try:
                print(f"Attempting generation with {name}...")
                result = self.call_model_api(model, prompt)
                
                # Success!
                self.quota_mgr.increment_usage(model_id)
                return result
                
            except Exception as e:
                error_msg = f"{name} failed: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                # Continue to next model
        
        # If we get here, all failed
        raise Exception("All configured models failed.\n" + "\n".join(errors))

    def call_model_api(self, model_conf, prompt):
        """
        Generic OpenAI-compatible API call.
        """
        raw_key = model_conf.get('api_key', '')
        
        # Deobfuscate
        from .config import deobfuscate_key
        if raw_key.startswith("ENC:"):
            api_key = deobfuscate_key(raw_key[4:])
        else:
            api_key = raw_key

        endpoint = model_conf.get('endpoint') # e.g. https://api.openai.com/v1/chat/completions
        model_name = model_conf.get('model_name') # e.g. gpt-4
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Basic timeout 60s
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            # Check for specific quota errors if possible to flag specifically?
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        data = response.json()
        try:
            content = data['choices'][0]['message']['content']
            return content
        except (KeyError, IndexError):
            raise Exception("Unexpected API response format.")
