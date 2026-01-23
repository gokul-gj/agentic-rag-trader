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
        print("✅ [LLM Client] OpenAI Client Initialized Successfully")
    else:
        print("❌ [LLM Client] OPENAI_API_KEY not found in environment")
except Exception as e:
    print(f"❌ [LLM Client] OpenAI Client Init Failed: {e}")

# 2. Setup Groq (for Llama 3)
try:
    if os.environ.get("GROQ_API_KEY"):
        client_groq = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
        )
        print("✅ [LLM Client] Groq Client Initialized Successfully (Llama 3 Ready)")
    else:
        print("⚠️ [LLM Client] GROQ_API_KEY not found. Llama 3 requests will fallback to OpenAI.")
except Exception as e:
    print(f"❌ [LLM Client] Groq Client Init Failed: {e}")

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
        error_msg = "❌ No LLM Client initialized. Check that API keys are set in .env file."
        print(error_msg)
        return f"Error: {error_msg}"

    if not active_model:
         active_model = "gpt-4-turbo"

    try:
        provider_name = "GROQ" if active_client == client_groq else "OPENAI"
        print(f"🔄 [LLM Client] Querying {provider_name}: {active_model}")
        print(f"   System: {system_prompt[:80]}...")
        print(f"   User: {user_prompt[:100]}...")
        
        response = active_client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        print(f"✅ [LLM Client] Received response ({len(result)} chars)")
        return result
        
    except Exception as e:
        error_details = f"❌ Error calling LLM ({active_model}): {str(e)}"
        print(error_details)
        print(f"   Error Type: {type(e).__name__}")
        # Return error to prevent silent failures
        return f"Error calling LLM: {str(e)}"

def mock_query_llm(system_prompt: str, user_prompt: str) -> str:
    """Fallback for testing without API keys."""
    return f"[MOCK LLM RESPONSE] Based on {user_prompt[:20]}... Strategy looks good."
