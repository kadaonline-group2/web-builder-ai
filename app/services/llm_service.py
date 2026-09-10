import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(api_key=os.getenv("LLM_API_KEY"))


def ask_llm(user_message: str) -> str:
    model = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.choices[0].message.content
