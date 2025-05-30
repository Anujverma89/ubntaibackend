import os
from langchain.chat_models import init_chat_model



# RAG-enabled query function
def ask_gemini(prompt: str) -> str:

    llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    response = llm.invoke(prompt)
    return response.content