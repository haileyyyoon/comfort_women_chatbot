"""
rag.py
------
Core chatbot logic: takes a user question (plus recent chat history),
retrieves relevant passages via tools.get_response, and asks the LLM to
answer using only that retrieved information.
"""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import get_response

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You can call a function to retrieve information about comfort women "
    "(Japanese military sexual slavery victims) that is most relevant to "
    "the user's question. Always call this function before answering a "
    "question that requires factual, historical, or biographical information. "
    "The knowledge base is written in English, so when you call the function, "
    "translate the user's question into English and pass the English version "
    "as the `question` argument, even if the user wrote in another language."
)


def _language_directive(language: str) -> str:
    """Return the instruction that controls which language the answer is written in."""
    if not language or language.lower() in ("auto", "detect"):
        return (
            "Write your entire answer in the same language the user used in their "
            "most recent question. If you are unsure, default to English."
        )
    return (
        f"Write your entire answer in {language}, regardless of the language of the "
        "source material below. Translate the retrieved English facts into "
        f"{language} naturally and accurately."
    )


def _answer_instructions(language: str) -> str:
    """Build the system prompt for the final, grounded answer."""
    return (
        "You are Nanumi (나누미), the chatbot guide of the House of Sharing (나눔의 집), "
        "a museum documenting the history of Japan's wartime military 'comfort women' "
        "(military sexual slavery) system. Your readers are often visitors from other "
        "countries who are new to this topic.\n\n"
        "Rules:\n"
        "1. Answer ONLY using the information provided by the function call below. "
        "Do not use any outside knowledge, and never invent names, dates, numbers, "
        "or events that are not in the provided material.\n"
        "2. If the provided information does not contain the answer, tell the user "
        "that this specific detail is not in the museum's records, and, if helpful, "
        "suggest a related question you can answer.\n"
        "3. Assume the reader may not know the basic background. Briefly explain key "
        "terms and context (only as supported by the provided material) so a newcomer "
        "can understand, but stay focused on what was actually asked.\n"
        "4. Aim for a clear, well-organized answer of one to three short paragraphs. "
        "Be thorough where the material allows, but do not pad.\n"
        "5. Treat the subject and the survivors with the utmost seriousness, dignity, "
        "and respect. Always use polite, respectful language, and never refer to "
        "survivors in casual or diminishing terms. When answering in Korean, always "
        "use formal polite speech (존댓말, -습니다/-세요 endings) and refer to "
        "survivors with respectful honorific expressions such as '피해자 할머니들' "
        "or '김학순 할머니'. When answering in Japanese, use polite です/ます forms. "
        "Avoid graphic detail that is not necessary for historical understanding.\n\n"
        f"{_language_directive(language)}"
    )

FUNCTIONS = [
    {
        "type": "function",
        "name": "get_response",
        "description": (
            "Get the information about comfort women that is most appropriate "
            "for the user's question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The user's question about comfort women.",
                }
            },
            "required": ["question"],
        },
    }
]


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Check your .env file.")
    return OpenAI(api_key=api_key)


def _extract_chunks(pinecone_results: dict) -> list[str]:
    chunks = []
    for match in pinecone_results.get("matches", []):
        metadata = match.get("metadata", {}) or match.get("fields", {})
        chunk = metadata.get("chunk_text") or match.get("chunk_text", "")
        if chunk:
            chunks.append(chunk)
    return chunks


def chatbot_response(
    user_input: str,
    chat_history: list[dict] | None = None,
    language: str = "auto",
) -> str:
    if chat_history is None:
        chat_history = []

    client = _client()
    input_messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + chat_history
        + [{"role": "user", "content": user_input}]
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=input_messages,
            functions=FUNCTIONS,
            function_call="auto",
        )
    except Exception as exc:
        logger.exception("LLM call failed")
        return f"Sorry, I ran into an error talking to the language model: {exc}"

    message = response.choices[0].message

    if not message.function_call:
        return message.content

    func_name = message.function_call.name
    if func_name != "get_response":
        return f"Sorry, I don't know how to handle '{func_name}'."

    try:
        args = json.loads(message.function_call.arguments)
    except (json.JSONDecodeError, TypeError):
        logger.exception("Could not parse function call arguments")
        return "Sorry, something went wrong while processing your question."

    try:
        retrieval_results = get_response(**args)
    except Exception as exc:
        logger.exception("Retrieval failed")
        return f"Sorry, I couldn't retrieve information right now: {exc}"

    top_chunks = _extract_chunks(retrieval_results)
    combined_context = "\n\n".join(top_chunks)

    followup_messages = (
        [{"role": "system", "content": _answer_instructions(language)}]
        + chat_history
        + [
            {"role": "user", "content": user_input},
            message,
            {
                "role": "function",
                "name": func_name,
                "content": combined_context or "No relevant information was found.",
            },
        ]
    )

    try:
        followup = client.chat.completions.create(
            model=MODEL,
            messages=followup_messages,
            max_tokens=700,
        )
    except Exception as exc:
        logger.exception("LLM follow-up call failed")
        return f"Sorry, I ran into an error generating a response: {exc}"

    return followup.choices[0].message.content


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    history: list[dict] = []
    print("Comfort women history chatbot (type 'exit' to quit)\n")
    while True:
        user_input = input("User: ")
        if user_input.strip().lower() in ("exit", "end", "bye"):
            print("Bot: Goodbye!")
            break
        history.append({"role": "user", "content": user_input})
        reply = chatbot_response(user_input, history)
        history.append({"role": "assistant", "content": reply})
        print("Bot:", reply)
