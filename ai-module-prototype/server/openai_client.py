from __future__ import annotations

import os
import re

import httpx

from .models import LlmTutorInput, LlmTutorOutput


DEFAULT_BASE_URL = "https://api.openai.com/v1"


async def generate_tutor_response(input_data: LlmTutorInput) -> LlmTutorOutput:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return generate_fallback_response(input_data)

    base_url = os.getenv("OPENAI_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "temperature": 0.25 if input_data.revealSolution else 0.45,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Socratic tutor. Help students reason "
                            "through exercises. Do not reveal a final answer unless "
                            "the current strategy explicitly says to provide a full "
                            "solution."
                        ),
                    },
                    {"role": "user", "content": build_tutor_prompt(input_data)},
                ],
            },
        )

    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(
            f"LLM request failed with {response.status_code}: {response.text}"
        )

    data = response.json()
    raw_content = (
        data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    )

    if not raw_content:
        raise RuntimeError("LLM returned an empty tutor response.")

    return split_follow_up(raw_content)


def build_tutor_prompt(input_data: LlmTutorInput) -> str:
    prior_hints = "\n\n".join(
        f"Level {message.hintLevel or '?'}: {message.content}"
        for message in input_data.priorAssistantMessages
        if message.role == "assistant"
    )

    return "\n\n".join(
        [
            f"Problem statement:\n{input_data.problemStatement}",
            "Student's current work:\n"
            + (
                input_data.studentWork
                or "The student has not written any work yet."
            ),
            f"Student's question:\n{input_data.studentQuestion}",
            f"Hints already given:\n{prior_hints}"
            if prior_hints
            else "Hints already given: none.",
            (
                f"Current hint strategy: Level {input_data.strategy.level} - "
                f"{input_data.strategy.label}"
            ),
            input_data.strategy.instruction,
            "Respond in 2-5 concise sentences. Keep the tone encouraging and precise.",
            (
                "If this is not the full solution level, avoid final answers, "
                "completed derivations, or code that solves the whole task."
            ),
            "End with one short guiding question when useful.",
        ]
    )


def split_follow_up(content: str) -> LlmTutorOutput:
    sentences = re.findall(r"[^.!?]+[.!?]+|\S+$", content) or [content]
    last_sentence = sentences[-1].strip()

    if last_sentence.endswith("?") and len(sentences) > 1:
        return LlmTutorOutput(
            content=" ".join(sentence.strip() for sentence in sentences[:-1]).strip(),
            followUpQuestion=last_sentence,
        )

    return LlmTutorOutput(content=content)


def generate_fallback_response(input_data: LlmTutorInput) -> LlmTutorOutput:
    if input_data.revealSolution:
        return LlmTutorOutput(
            content=(
                "Work from the definitions in the problem, write down each known "
                "quantity, and connect them with the relevant rule or theorem. "
                "Then carry out the algebra or logical steps one at a time, "
                "checking that each step follows from the previous one. If there "
                "is a numerical or final form required, substitute only at the end "
                "so the reasoning stays visible."
            ),
            followUpQuestion=(
                "Which step in that outline can you justify first from the problem "
                "statement?"
            ),
        )

    fallback_by_level = {
        1: LlmTutorOutput(
            content=(
                "Pause on the part where your reasoning first becomes uncertain "
                "and compare it with the exact wording of the problem. There is "
                "usually one condition or constraint that tells you what the next "
                "move should respect."
            ),
            followUpQuestion="What information in the statement have you not used yet?",
        ),
        2: LlmTutorOutput(
            content=(
                "This looks like a moment to name the concept that links your "
                "current work to the goal. Look for a definition, invariant, "
                "formula, or theorem that transforms what you already know into "
                "the form the problem asks for."
            ),
            followUpQuestion=(
                "Which concept from the lesson seems closest to the shape of this "
                "problem?"
            ),
        ),
        3: LlmTutorOutput(
            content=(
                "Try choosing a strategy before calculating: introduce a helpful "
                "variable, draw a smaller case, isolate the unknown, or rewrite "
                "the expression so the target quantity appears. The next useful "
                "step is probably a setup step, not the final computation."
            ),
            followUpQuestion=(
                "Can you rewrite your current line so the desired quantity is "
                "explicit?"
            ),
        ),
        4: LlmTutorOutput(
            content=(
                "Take the strongest relationship you have already written and "
                "apply it directly to the unknown part. Keep all symbols visible, "
                "then simplify only the side of the equation or argument that "
                "blocks your progress."
            ),
            followUpQuestion=(
                "After applying that relationship, what single term or claim "
                "remains unresolved?"
            ),
        ),
        5: LlmTutorOutput(
            content=(
                "A near-complete path is: identify the target, write the governing "
                "relationship, substitute the known parts from the statement, "
                "isolate the missing part, and then verify the result against the "
                "original condition. Do the verification before treating your "
                "answer as final."
            ),
            followUpQuestion="Where in that outline does your current work fit?",
        ),
    }

    return fallback_by_level.get(input_data.strategy.level, fallback_by_level[5])
