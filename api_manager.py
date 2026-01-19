import json
import urllib.request
import urllib.error
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
        Generic OpenAI-compatible API call using urllib (built into Python).
        Compatible with Calibre's embedded Python environment.
        """
        raw_key = model_conf.get('api_key', '')
        
        # Deobfuscate
        from .config import deobfuscate_key
        if raw_key.startswith("ENC:"):
            api_key = deobfuscate_key(raw_key[4:])
        else:
            api_key = raw_key

        endpoint = model_conf.get('endpoint')  # e.g. https://api.openai.com/v1/chat/completions
        model_name = model_conf.get('model_name')  # e.g. gpt-4
        
        # Get max_tokens from prefs
        max_tokens = prefs.get('max_tokens', 4096)
        
        # Check if prompt contains system/user separation (marked by special delimiter)
        # If prompt is a tuple/list of (system, user), use both; otherwise treat as single user message
        if isinstance(prompt, (list, tuple)) and len(prompt) == 2:
            system_prompt, user_prompt = prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        else:
            # Legacy single prompt format
            messages = [
                {"role": "user", "content": prompt}
            ]
        
        # Prepare request payload
        payload = {
            "messages": messages,
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        # Convert payload to JSON bytes
        data = json.dumps(payload).encode('utf-8')
        
        # Create request with headers
        request = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method='POST'
        )
        
        try:
            # Send request with 60s timeout
            with urllib.request.urlopen(request, timeout=60) as response:
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data)
                
                # Extract content from response
                try:
                    content = result['choices'][0]['message']['content']
                    return content
                except (KeyError, IndexError):
                    raise Exception("Unexpected API response format.")
                    
        except urllib.error.HTTPError as e:
            # HTTP error (4xx, 5xx)
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise Exception(f"API Error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            # Network error
            raise Exception(f"Network Error: {str(e.reason)}")
        except json.JSONDecodeError as e:
            # JSON parsing error
            raise Exception(f"Invalid JSON response: {str(e)}")

