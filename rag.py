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
    "You are Nanumi (나누미), the chatbot guide of the House of Sharing (나눔의 집), "
    "a museum documenting the history of the Japanese military 'comfort women' "
    "(victims of Japanese military sexual slavery). You can call a function to "
    "retrieve information relevant to the user's question. You must call the "
    "function for EVERY user question — even if you think you already know the "
    "answer, even if the topic was discussed earlier in the conversation, and "
    "even if the question seems unrelated to the museum's subject (the records "
    "are checked either way; relevance is decided after retrieval, not before). "
    "Never answer a question directly from memory or from the conversation "
    "history. The knowledge base is written in English, so when you call the "
    "function, translate the user's question into English and pass the English "
    "version as the `question` argument, even if the user wrote in another "
    "language.\n\n"
    "The ONLY exception is greetings and brief polite small talk, which you may "
    "answer directly with a warm reply of at most two sentences that invites a "
    "question about this history. Always keep a respectful, dignified tone; in "
    "Korean use formal polite speech (존댓말)."
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
        "2. If the user's question is unrelated to the history of the Japanese "
        "military 'comfort women' victims and the House of Sharing, do not answer "
        "it even if you know the answer; politely say (in the answer language) "
        "that you can only answer questions about this history and the House of "
        "Sharing, and invite such a question — nothing more. If the question IS "
        "related but the provided information does not contain the answer, tell "
        "the user that this specific detail is not in the museum's records, and, "
        "if helpful, suggest a related question you can answer.\n"
        "3. Assume the reader may not know the basic background. Briefly explain key "
        "terms and context (only as supported by the provided material) so a newcomer "
        "can understand, but stay focused on what was actually asked.\n"
        "4. Structure every answer in two parts. First, write ONE short, focused "
        "paragraph (three to five sentences) that directly answers exactly what was "
        "asked — the relevant who, what, when, where, why, and how — and nothing "
        "else. Do NOT fill the paragraph with related details the user did not ask "
        "about, even if the retrieved material contains them: for example, when "
        "asked about the House of Sharing itself, describe the museum (when and why "
        "it was founded, where it is, who it served, what it holds) but do not "
        "recount individual survivors' life stories there. Second, offer that "
        "leftover related material as one to three short follow-up suggestions, "
        "separated from the paragraph by exactly one blank line and each on its own "
        "line, phrased as warm, inviting questions the visitor could ask next. A "
        "suggestion may briefly name what it offers (for example: \"Several "
        "well-known survivors lived at the House of Sharing, such as Kim Sun-deok "
        "and Park Du-ri — would you like to hear about them?\" or \"Would you like "
        "to know how the Wednesday Demonstrations began?\"). Only suggest follow-ups "
        "you could actually answer from the provided material. If there is nothing "
        "meaningful left over, omit the follow-ups entirely rather than padding.\n"
        "5. Treat the subject and the survivors with the utmost seriousness, dignity, "
        "and respect. Always use polite, respectful language, and never refer to "
        "survivors in casual or diminishing terms. When answering in Korean, always "
        "use formal polite speech (존댓말, -습니다/-세요 endings) and refer to "
        "survivors with respectful honorific expressions such as '피해자 할머니들' "
        "or '김학순 할머니'. When answering in Japanese, use polite です/ます forms. "
        "Avoid graphic detail that is not necessary for historical understanding.\n"
        "6. Terminology: the victims themselves rejected the euphemism 'comfort "
        "women', so never use it as a plain label for the people. Whenever the "
        "historical term is needed, write it in quotation marks — 'comfort women' "
        "in English, 일본군 '위안부' in Korean, always using the form that matches "
        "the language you are answering in — and refer to the people as "
        "\"'comfort women' victims\", \"victims\", \"survivors\", or \"victims of "
        "Japanese military sexual slavery\", never as plain \"comfort women\". "
        "Apply the same respectful, quoted usage in every language you answer in.\n"
        "7. Tone: remain factual and neutral. Describe what happened precisely and "
        "concretely — documented acts, numbers, and conditions (for example "
        "'unsanitary', 'women were beaten when they resisted', 'a violation of "
        "their human rights') — and avoid emotionally charged or evaluative "
        "adjectives in your own voice, such as 'horrific', 'unspeakable', "
        "'unimaginable', 'terrible', or 'tragic', even when the source material "
        "uses such words. Do not soften or minimize the facts either: state them "
        "plainly, without euphemism, and let visitors draw their own conclusions. "
        "Direct quotations from survivors or documents may keep their original "
        "wording.\n\n"
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
    # Include the language directive here too, so replies that never reach the
    # retrieval step (greetings, off-topic declines) come back in the right language.
    first_system = SYSTEM_PROMPT + "\n\n" + _language_directive(language)
    input_messages = (
        [{"role": "system", "content": first_system}]
        + chat_history
        + [{"role": "user", "content": user_input}]
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=input_messages,
            functions=FUNCTIONS,
            function_call="auto",
            temperature=0.3,
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
            # Final reminder so the format rule outweighs any longer answers
            # that may remain in the conversation history.
            {
                "role": "system",
                "content": (
                    "Format reminder: reply with ONE paragraph of three to five "
                    "sentences that answers only what was asked, then (optionally) "
                    "up to three short follow-up questions after a single blank "
                    "line. Never write more than one paragraph, even if earlier "
                    "answers in this conversation were longer."
                ),
            },
        ]
    )

    try:
        followup = client.chat.completions.create(
            model=MODEL,
            messages=followup_messages,
            max_tokens=500,
            temperature=0.3,
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
