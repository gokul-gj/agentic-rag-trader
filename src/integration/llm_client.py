import os
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize client
# User must set OPENAI_API_KEY in environment variables
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print(f"Warning: OpenAI Client could not be initialized. {e}")
    client = None

def query_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4-turbo") -> str:
    """
    Wrapper to call OpenAI API.
    """
    if not client:
        return "Error: OpenAI Client not initialized. Please set OPENAI_API_KEY."

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

def mock_query_llm(system_prompt: str, user_prompt: str) -> str:
    """Fallback for testing without API keys."""
    return f"[MOCK LLM RESPONSE] Based on {user_prompt[:20]}... Strategy looks good."
