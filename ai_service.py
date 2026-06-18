import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

SYSTEM_PROMPT = """
Jesteś nauczycielem sokratejskim.

Nigdy nie podawaj gotowego rozwiązania.
Zamiast tego:
- naprowadzaj pytaniami,
- wskazuj błędy,
- sugeruj kolejny krok,
- odpowiadaj po polsku.
"""

class PjaSenseiAI:
    def __init__(self):
        self.client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.history = []

    def message_pja_sensei(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            *self.history,
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=messages,
            temperature=0.4,
            max_tokens=500
        )
            
        answer = response.choices[0].message.content
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": answer})

        return answer