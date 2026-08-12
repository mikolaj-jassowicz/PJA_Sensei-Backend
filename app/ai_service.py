import os
import uuid
from dataclasses import dataclass, field

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


@dataclass
class Conversation:
    problem: str
    progress: str = ""
    messages: list[dict] = field(default_factory=list)


class UnknownConversation(Exception):
    pass


class PjaSenseiAI:
    MAX_HISTORY = 20

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.conversations: dict[str, Conversation] = {}

    def start_conversation(self, problem: str, progress: str = "") -> str:
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = Conversation(problem, progress)
        return conversation_id

    def send_message(
        self, conversation_id: str, question: str, progress: str | None = None
    ) -> str:
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            raise UnknownConversation(conversation_id)

        if progress is not None:
            conversation.progress = progress

        conversation.messages.append({"role": "user", "content": question})

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": self._context(conversation)},
            *conversation.messages[-self.MAX_HISTORY:],
        ]

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=messages,
            temperature=0.4,
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        if answer is None:
            conversation.messages.pop()
            raise ValueError("Model nie zwrócił odpowiedzi. Spróbuj ponownie.")

        conversation.messages.append({"role": "assistant", "content": answer})
        return answer

    def _context(self, conversation: Conversation) -> str:
        return f"""
                Zadanie, nad którym pracuje student:
                {conversation.problem}

                Aktualny stan jego rozwiązania:
                {conversation.progress or "(student jeszcze nic nie napisał)"}
                """