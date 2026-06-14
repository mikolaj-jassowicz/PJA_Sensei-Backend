from pydantic import BaseModel
from ai_service import PjaSenseiAI
from fastapi import FastAPI

app = FastAPI()

ai = PjaSenseiAI()


class HintRequest(BaseModel):
    problem: str
    progress: str
    question: str


@app.post("/hint")
def get_hint(request: HintRequest):

    prompt = f"""
    Zadanie:
    {request.problem}

    Dotychczasowe rozwiązanie:
    {request.progress}

    Pytanie studenta:
    {request.question}
    """

    hint = ai.generate_hint(prompt)

    return {
        "hint": hint
    }