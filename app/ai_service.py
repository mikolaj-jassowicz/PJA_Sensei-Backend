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
        self.conversations: dict[str, list[dict]] = {}

    def message_pja_sensei(self, conversation_id: str, prompt: str) -> str:
        history = self.conversations.setdefault(conversation_id, [])

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            *history,
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

        if answer is None:
            raise ValueError("Model nie zwrócił odpowiedzi. Spróbuj ponownie.")

        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": answer})

        return answer