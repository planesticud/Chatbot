from langchain_cohere.chat_models import ChatCohere
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm(
    temperature,
    max_tokens,
    llm_provier = 'cohere'):
    
    if llm_provier == 'cohere':
        return cohere_llm(
            cohere_api_key=os.getenv('COHERE_API_KEY'),
            temperature=temperature,
            max_tokens=max_tokens)

def cohere_llm(
    cohere_api_key,
    model = "command-nightly",
    temperature = 0.2,
    max_tokens = 400):
    
    return ChatCohere(
            model = model,
            temperature = temperature,
            cohere_api_key = cohere_api_key,
            max_tokens = max_tokens
        )