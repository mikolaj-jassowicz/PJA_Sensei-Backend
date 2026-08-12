from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.ai_service import PjaSenseiAI, UnknownConversation

app = FastAPI()
ai = PjaSenseiAI()


class StartRequest(BaseModel):
    problem: str
    progress: str = ""


class MessageRequest(BaseModel):
    question: str
    progress: str | None = None


@app.post("/conversations")
def start_conversation(request: StartRequest):
    return {"conversation_id": ai.start_conversation(request.problem, request.progress)}


@app.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, request: MessageRequest):
    try:
        answer = ai.send_message(conversation_id, request.question, request.progress)
    except UnknownConversation:
        raise HTTPException(status_code=404, detail="Nie ma takiej konwersacji")
    return {"answer": answer}


@app.get("/conversations/{conversation_id}")
def inspect_conversation(conversation_id: str):
    conversation = ai.conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Nie ma takiej konwersacji")
    return {
        "problem": conversation.problem,
        "message_count": len(conversation.messages),
        "messages": conversation.messages,
    }
