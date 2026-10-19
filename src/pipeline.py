import asyncio
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from langchain_groq import ChatGroq

from src.config import HR_SYSTEM_PROMPT, SENSITIVE_OUTPUT_PATTERNS
from src.guards import build_rails, parse_nemo_response
from src.rag import retrieve


# Run async NeMo calls in a worker thread.
_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="nemo",
)


def check_output(text: str) -> list[str]:
    """
    Check generated answers for sensitive information.

    Returns a list of matched safety-rule names.
    """
    issues = []

    for rule_name, pattern in SENSITIVE_OUTPUT_PATTERNS.items():
        try:
            if re.search(pattern, text or ""):
                issues.append(rule_name)
        except re.error:
            # Avoid crashing the application if a regex is invalid.
            issues.append(f"invalid_pattern:{rule_name}")

    return issues


def _run_nemo_check(
    message: str,
    groq_key: str,
    guard_model: str,
) -> str:
    """
    Run NeMo Guardrails in a worker thread.

    Exceptions are handled by run_pipeline(), which fails closed.
    """
    guard_llm = ChatGroq(
        api_key=groq_key,
        model=guard_model,
        temperature=0,
    )

    rails = build_rails(guard_llm)

    result = asyncio.run(
        rails.generate_async(
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ]
        )
    )

    if isinstance(result, dict):
        return str(
            result.get("content")
            or result.get("response")
            or ""
        )

    return str(result)


def run_pipeline(
    message: str,
    groq_key: str,
    guard_model: str,
    chat_model: str,
    vectorstore,
) -> tuple[str, dict]:
    """
    Execute the HR assistant pipeline:

    1. Validate the user input.
    2. Run NeMo Guardrails.
    3. Retrieve relevant HR policies using FAISS.
    4. Generate an answer with Groq.
    5. Check the output for sensitive information.

    Returns:
        tuple[str, dict]: The answer and execution trace.
    """

    total_start = time.time()

    trace = {
        "rail": {},
        "retrieval": {
            "chunks": [],
            "ms": 0,
            "error": None,
        },
        "generation": {
            "ms": 0,
            "model": chat_model,
            "error": None,
        },
        "output_rail": {
            "issues": [],
        },
        "total_ms": 0,
    }

    if not isinstance(message, str) or not message.strip():
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )
        return "Please enter a question.", trace

    message = message.strip()

    if not groq_key:
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )
        return "Please enter your Groq API key in the sidebar.", trace

    rail_start = time.time()
    nemo_error = None

    future = _executor.submit(
        _run_nemo_check,
        message,
        groq_key,
        guard_model,
    )

    try:
        raw = future.result(timeout=60)

    except Exception as exc:
        nemo_error = str(exc)
        raw = ""

        trace["rail"] = {
            "blocked": True,
            "reason": "guardrails_error",
            "dialog": False,
            "ms": round(
                (time.time() - rail_start) * 1000
            ),
            "model": guard_model,
            "error": nemo_error,
        }

        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )

        # Fail closed: do not continue to RAG or answer generation.
        return (
            "I couldn't complete the safety check. "
            "Please try again later or contact HR at hr@acmecorp.com.",
            trace,
        )

    # Parse the guardrails response.
    parsed = parse_nemo_response(raw)

    # Expected return:
    # text, blocked, reason, dialog, needs_rag
    try:
        (
            rail_text,
            blocked,
            reason,
            dialog,
            needs_rag,
        ) = parsed
    except (TypeError, ValueError):
        trace["rail"] = {
            "blocked": True,
            "reason": "invalid_guardrails_response",
            "dialog": False,
            "ms": round(
                (time.time() - rail_start) * 1000
            ),
            "model": guard_model,
            "error": "Unexpected response from parse_nemo_response().",
        }

        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )

        return (
            "I couldn't verify that request safely. "
            "Please try again or contact HR at hr@acmecorp.com.",
            trace,
        )

    trace["rail"] = {
        "blocked": bool(blocked),
        "reason": reason,
        "dialog": bool(dialog),
        "ms": round(
            (time.time() - rail_start) * 1000
        ),
        "model": guard_model,
        "error": None,
    }

    # Block unsafe requests.
    if blocked:
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )
        return (
            rail_text
            or "This request cannot be processed under the HR assistant's safety rules.",
            trace,
        )

    # Return direct guardrails responses, such as greetings.
    if dialog:
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )
        return rail_text, trace

    # Continue only if guardrails explicitly allow the RAG flow.
    if not needs_rag:
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )
        return (
            rail_text
            or "I couldn't determine a safe response to that request.",
            trace,
        )

    retrieval_start = time.time()

    try:
        chunks = retrieve(
            message,
            vectorstore,
            k=3,
        )

        trace["retrieval"]["chunks"] = chunks

    except Exception as exc:
        trace["retrieval"]["error"] = str(exc)
        trace["retrieval"]["ms"] = round(
            (time.time() - retrieval_start) * 1000
        )
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )

        return (
            "I couldn't retrieve the HR policies right now. "
            "Please try again later or contact hr@acmecorp.com.",
            trace,
        )

    trace["retrieval"]["ms"] = round(
        (time.time() - retrieval_start) * 1000
    )

    # Build the policy context.
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "HR Policy")
        content = chunk.get("content", "").strip()

        if content:
            context_parts.append(
                f"[Policy excerpt {index}: {source}]\n{content}"
            )

    context_text = (
        "\n\n".join(context_parts)
        if context_parts
        else "No relevant policy excerpts were retrieved."
    )

    generation_start = time.time()

    try:
        chat_llm = ChatGroq(
            api_key=groq_key,
            model=chat_model,
            temperature=0,
        )

        system_prompt = HR_SYSTEM_PROMPT.format(
            context=context_text
        )

        response = chat_llm.invoke(
            [
                ("system", system_prompt),
                ("human", message),
            ]
        )

        answer = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

    except Exception as exc:
        trace["generation"]["error"] = str(exc)
        trace["generation"]["ms"] = round(
            (time.time() - generation_start) * 1000
        )
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )

        return (
            "I couldn't generate an answer right now. "
            "Please try again later or contact hr@acmecorp.com.",
            trace,
        )

    trace["generation"]["ms"] = round(
        (time.time() - generation_start) * 1000
    )

    output_issues = check_output(answer)
    trace["output_rail"]["issues"] = output_issues

    if output_issues:
        trace["total_ms"] = round(
            (time.time() - total_start) * 1000
        )

        return (
            "The generated response was withheld because it "
            "triggered a sensitive-information safety check. "
            "Please contact hr@acmecorp.com for assistance.",
            trace,
        )

    trace["total_ms"] = round(
        (time.time() - total_start) * 1000
    )

    return answer, trace
