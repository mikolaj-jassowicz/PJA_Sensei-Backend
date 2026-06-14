import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


class PjaSenseiAI:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

    def generate_hint(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="""
                Jesteś nauczycielem sokratejskim.

                Student przekazuje:
                - treść zadania,
                - swoje dotychczasowe rozwiązanie,
                - pytanie.

                Zasady:
                - odpowiadaj wyłącznie po polsku,
                - dawaj wskazówki,
                - nie podawaj gotowego rozwiązania.
                """
            ),
        )

        return response.text