from app.ai_service import PjaSenseiAI
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
ai = PjaSenseiAI()

class HintRequest(BaseModel):
    conversation_id: str
    problem: str
    progress: str
    question: str


@app.post("/hint")
def discuss_a_problem(request: HintRequest):
    prompt = f"""
    Zadanie:
    {request.problem}

    Dotychczasowe rozwiązanie:
    {request.progress}

    Pytanie studenta:
    {request.question}
    """

    pja_sensei_answer = ai.message_pja_sensei(request.conversation_id, prompt)

    return pja_sensei_answer
