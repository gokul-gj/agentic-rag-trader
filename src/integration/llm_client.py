import os
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
client_openai = None
client_groq = None

# 1. Setup OpenAI
try:
    if os.environ.get("OPENAI_API_KEY"):
        client_openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    else:
        print("Warning: OPENAI_API_KEY not found.")
except Exception as e:
    print(f"Warning: OpenAI Client Init Failed: {e}")

# 2. Setup Groq (for Llama 3)
try:
    if os.environ.get("GROQ_API_KEY"):
        client_groq = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
        )
        print("--- [LLM Client] Groq Client Initialized (Llama 3 Ready) ---")
    else:
        print("Info: GROQ_API_KEY not found. Llama 3 requests will fallback to OpenAI.")
except Exception as e:
    print(f"Warning: Groq Client Init Failed: {e}")

def query_llm(system_prompt: str, user_prompt: str, model: str = None, provider: str = "openai") -> str:
    """
    Wrapper to call LLM APIs (OpenAI or Groq).
    
    Args:
        system_prompt: The system instruction.
        user_prompt: The user query.
        model: Optional model name override.
        provider: 'openai' or 'groq'.
    """
    active_client = client_openai
    active_model = model
    
    # Provider Selection Logic
    if provider == "groq":
        if client_groq:
            active_client = client_groq
            if not active_model:
                active_model = "llama-3.3-70b-versatile" # Default strong Llama 3.3 model on Groq
        else:
            print(f"Warning: Groq requested but not available. Falling back to OpenAI.")
            active_client = client_openai
            # Do NOT use the llama model name for OpenAI, fallback to GPT default
            active_model = "gpt-4-turbo" 
            
    if not active_client:
        return "Error: No LLM Client initialized (Check API Keys)."

    if not active_model:
         active_model = "gpt-4-turbo"

    try:
        print(f"--- [LLM Client] Querying {provider.upper() if active_client == client_groq else 'OPENAI'} : {active_model} ---")
        response = active_client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM ({active_model}): {str(e)}")
        # If Groq fails, maybe try OpenAI fallback automatically? 
        # For now, just return error to avoid infinite loops or cost surprises.
        return f"Error calling LLM: {str(e)}"

def mock_query_llm(system_prompt: str, user_prompt: str) -> str:
    """Fallback for testing without API keys."""
    return f"[MOCK LLM RESPONSE] Based on {user_prompt[:20]}... Strategy looks good."
