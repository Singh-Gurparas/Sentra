import os
import requests

class SuggestionEngine:
    """
    Uses OpenAI API to generate improved prompts when vulnerabilities are detected.
    """
    
    @classmethod
    def suggest_improvement(cls, original_prompt: str, vulnerabilities: list) -> str:
        """
        Calls OpenAI API to get a safer prompt.
        Expects OPENAI_API_KEY environment variable.
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return "Please set OPENAI_API_KEY to get automated suggestions."
            
        vuln_descriptions = "\\n".join([f"- {v.get('description')}" for v in vulnerabilities])
        
        system_message = (
            "You are a security expert AI. Rewrite the following prompt to prevent "
            "prompt injection and other vulnerabilities. Keep the original intent."
        )
        
        user_message = (
            f"Original Prompt:\\n{original_prompt}\\n\\n"
            f"Detected Vulnerabilities:\\n{vuln_descriptions}\\n\\n"
            "Provide only the improved, secure prompt."
        )
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.2
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                return f"Error from OpenAI API: {response.text}"
                
        except Exception as e:
            return f"Error generating suggestion: {e}"
