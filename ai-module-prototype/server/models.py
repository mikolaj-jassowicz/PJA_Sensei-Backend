from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel


TutorAction = Literal["hint", "next", "solution"]
HintLevel = Literal[1, 2, 3, 4, 5, 6]
TutorRole = Literal["student", "assistant", "system"]
NextRecommendedAction = Literal[
    "continue_independently", "request_next_hint", "show_solution"
]


class TutorMessage(BaseModel):
    id: str
    role: TutorRole
    content: str
    hintLevel: Optional[HintLevel] = None
    createdAt: str
    isSolution: Optional[bool] = None
    followUpQuestion: Optional[str] = None


class TutorSessionSnapshot(BaseModel):
    sessionId: str
    problemStatement: str
    studentWork: str
    studentQuestion: str
    messages: list[TutorMessage]
    currentHintLevel: Union[HintLevel, Literal[0]]
    hintCount: int
    canRequestHint: bool
    solutionRevealed: bool
    nextRecommendedAction: NextRecommendedAction


class TutorRequestPayload(BaseModel):
    sessionId: Optional[str] = None
    problemStatement: str
    studentWork: str = ""
    studentQuestion: str
    action: TutorAction


class TutorResponsePayload(BaseModel):
    session: TutorSessionSnapshot
    latestMessage: TutorMessage


class HintStrategy(BaseModel):
    level: HintLevel
    label: str
    intent: str
    instruction: str


class TutorSession(BaseModel):
    sessionId: str
    problemStatement: str
    studentWork: str
    studentQuestion: str
    messages: list[TutorMessage]
    currentHintLevel: Union[HintLevel, Literal[0]]
    hintCount: int
    solutionRevealed: bool
    createdAt: str
    updatedAt: str


class LlmTutorInput(BaseModel):
    problemStatement: str
    studentWork: str
    studentQuestion: str
    priorAssistantMessages: list[TutorMessage]
    strategy: HintStrategy
    revealSolution: bool


class LlmTutorOutput(BaseModel):
    content: str
    followUpQuestion: Optional[str] = None
