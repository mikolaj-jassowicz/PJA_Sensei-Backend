from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .models import (
    HintLevel,
    HintStrategy,
    LlmTutorInput,
    TutorAction,
    TutorMessage,
    TutorRequestPayload,
    TutorResponsePayload,
    TutorSession,
    TutorSessionSnapshot,
)
from .openai_client import generate_tutor_response


MAX_HINT_LEVEL = 5
FINAL_SOLUTION_LEVEL = 6

HINT_STRATEGIES: dict[int, HintStrategy] = {
    1: HintStrategy(
        level=1,
        label="Subtle guidance",
        intent="Help the student notice what matters without naming the method.",
        instruction=(
            "Give a very subtle nudge. Ask the student to inspect assumptions, "
            "unused facts, or the target form. Do not name the exact method."
        ),
    ),
    2: HintStrategy(
        level=2,
        label="Relevant concepts",
        intent="Point toward concepts that may unlock the next idea.",
        instruction=(
            "Suggest the relevant concepts, definitions, or relationships. Keep "
            "it conceptual and avoid doing the student's next step."
        ),
    ),
    3: HintStrategy(
        level=3,
        label="Method or strategy",
        intent="Guide the student toward a concrete strategy.",
        instruction=(
            "Point toward a specific method or strategy. Explain why that strategy "
            "fits, but leave execution to the student."
        ),
    ),
    4: HintStrategy(
        level=4,
        label="Next concrete step",
        intent="Make the next action clear without finishing the problem.",
        instruction=(
            "Describe the next concrete step the student should take. You may "
            "include a partial setup, but do not complete the solution."
        ),
    ),
    5: HintStrategy(
        level=5,
        label="Almost complete outline",
        intent="Reveal the solution path while preserving the final work.",
        instruction=(
            "Provide a nearly complete solution outline. Avoid the final answer "
            "when possible, and ask the student to finish or verify it."
        ),
    ),
    6: HintStrategy(
        level=6,
        label="Full solution",
        intent=(
            "Give a complete answer because the user explicitly requested it or "
            "exhausted hints."
        ),
        instruction=(
            "Provide the full solution with clear reasoning. Keep it educational "
            "and point out the key idea the student should remember."
        ),
    ),
}


class HintManager:
    def __init__(self) -> None:
        self.sessions: dict[str, TutorSession] = {}

    async def handle_tutor_request(
        self, payload: TutorRequestPayload
    ) -> TutorResponsePayload:
        self._validate_payload(payload)

        session = self._get_or_create_session(payload)
        self._update_session_inputs(session, payload)

        reveal_solution = self._should_reveal_solution(session, payload.action)
        next_level = FINAL_SOLUTION_LEVEL if reveal_solution else self._next_hint_level(session)
        strategy = HINT_STRATEGIES[next_level]

        response = await generate_tutor_response(
            LlmTutorInput(
                problemStatement=session.problemStatement,
                studentWork=session.studentWork,
                studentQuestion=session.studentQuestion,
                priorAssistantMessages=[
                    message
                    for message in session.messages
                    if message.role == "assistant"
                ],
                strategy=strategy,
                revealSolution=reveal_solution,
            )
        )

        latest_message = TutorMessage(
            id=self._new_id(),
            role="assistant",
            content=response.content,
            hintLevel=strategy.level,
            createdAt=self._now_iso(),
            isSolution=reveal_solution,
            followUpQuestion=response.followUpQuestion,
        )

        session.messages.extend(
            [self._create_student_context_message(payload), latest_message]
        )
        session.currentHintLevel = strategy.level
        session.hintCount = (
            session.hintCount if reveal_solution else session.hintCount + 1
        )
        session.solutionRevealed = session.solutionRevealed or reveal_solution
        session.updatedAt = self._now_iso()

        return TutorResponsePayload(
            session=self._to_snapshot(session), latestMessage=latest_message
        )

    def reset_session(self, session_id: str) -> bool:
        return self.sessions.pop(session_id, None) is not None

    def _validate_payload(self, payload: TutorRequestPayload) -> None:
        if not payload.problemStatement.strip():
            raise ValueError("A problem statement is required.")

        if not payload.studentQuestion.strip():
            raise ValueError("A student question is required.")

    def _get_or_create_session(self, payload: TutorRequestPayload) -> TutorSession:
        session_id = payload.sessionId or self._new_id()
        existing = self.sessions.get(session_id)

        if existing:
            return existing

        now = self._now_iso()
        session = TutorSession(
            sessionId=session_id,
            problemStatement=payload.problemStatement,
            studentWork=payload.studentWork,
            studentQuestion=payload.studentQuestion,
            messages=[],
            currentHintLevel=0,
            hintCount=0,
            solutionRevealed=False,
            createdAt=now,
            updatedAt=now,
        )
        self.sessions[session_id] = session
        return session

    def _update_session_inputs(
        self, session: TutorSession, payload: TutorRequestPayload
    ) -> None:
        session.problemStatement = payload.problemStatement.strip()
        session.studentWork = payload.studentWork.strip()
        session.studentQuestion = payload.studentQuestion.strip()

    def _should_reveal_solution(
        self, session: TutorSession, action: TutorAction
    ) -> bool:
        if action == "solution" or session.solutionRevealed:
            return True

        return action == "next" and session.currentHintLevel >= MAX_HINT_LEVEL

    def _next_hint_level(self, session: TutorSession) -> HintLevel:
        if session.currentHintLevel == 0 or session.solutionRevealed:
            return 1

        return min(session.currentHintLevel + 1, MAX_HINT_LEVEL)  # type: ignore[return-value]

    def _create_student_context_message(
        self, payload: TutorRequestPayload
    ) -> TutorMessage:
        label = (
            "Student requested another hint"
            if payload.action == "next"
            else "Student asked for help"
        )

        return TutorMessage(
            id=self._new_id(),
            role="student",
            content=(
                f"{label}.\n\nCurrent work:\n"
                f"{payload.studentWork or '(none yet)'}\n\n"
                f"Question:\n{payload.studentQuestion}"
            ),
            createdAt=self._now_iso(),
        )

    def _to_snapshot(self, session: TutorSession) -> TutorSessionSnapshot:
        if session.solutionRevealed:
            next_recommended_action = "continue_independently"
        elif session.currentHintLevel >= MAX_HINT_LEVEL:
            next_recommended_action = "show_solution"
        elif session.currentHintLevel <= 2:
            next_recommended_action = "continue_independently"
        else:
            next_recommended_action = "request_next_hint"

        return TutorSessionSnapshot(
            sessionId=session.sessionId,
            problemStatement=session.problemStatement,
            studentWork=session.studentWork,
            studentQuestion=session.studentQuestion,
            messages=session.messages,
            currentHintLevel=session.currentHintLevel,
            hintCount=session.hintCount,
            canRequestHint=(
                not session.solutionRevealed
                and session.currentHintLevel < MAX_HINT_LEVEL
            ),
            solutionRevealed=session.solutionRevealed,
            nextRecommendedAction=next_recommended_action,
        )

    def _new_id(self) -> str:
        return uuid4().hex

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
