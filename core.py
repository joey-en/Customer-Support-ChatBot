import json
import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from mistralai import Mistral, UserMessage

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
DOCS_DIR = BASE_DIR / "documents"


@lru_cache(maxsize=64)
def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_inquiry(user_input: str, history: list[dict] | None) -> str:
    if not history:
        return user_input
    turns = history[-6:]
    lines = []
    for msg in turns:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    lines.append(f"User: {user_input}")
    return "Conversation history:\n" + "\n".join(lines) + "\n\nCurrent inquiry:\n" + user_input


def mistral_chat(prompt: str) -> str:
    client = Mistral(api_key=API_KEY)
    messages = [UserMessage(content=prompt)]
    response = client.chat.complete(model=MODEL, messages=messages)
    return response.choices[0].message.content.strip()


def normalize_intent(text: str) -> str:
    normalized = text.strip()
    valid = {
        "Technical Issue",
        "Feature Explanation",
        "System Architecture Explanation",
        "General Inquiry",
    }
    return normalized if normalized in valid else "General Inquiry"


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def strip_html_divs(text: str) -> str:
    if not isinstance(text, str):
        return text
    return re.sub(r"</?div[^>]*>", "", text)


def strip_markdown(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text.strip()


def summarize_issue(text: str) -> str:
    prompt = (
        "Summarize the technical issue below in 2-3 concise sentences. "
        "Focus on symptoms, context, and any mentioned errors. "
        "Do not add new information.\n\n"
        f"Issue:\n{text}\n\nSummary:"
    )
    return strip_markdown(mistral_chat(prompt))


def sanitize_issue_data(data: dict) -> dict:
    fields = [
        "issue_type",
        "video_length",
        "video_format",
        "error_message",
        "stage_of_failure",
        "device_or_environment",
        "urgency_level",
    ]
    sanitized = {}
    for field in fields:
        value = data.get(field, "Not specified") if isinstance(data, dict) else "Not specified"
        if value is None:
            value = "Not specified"
        if isinstance(value, str):
            value = value.strip() or "Not specified"
        sanitized[field] = value
    return sanitized


def generate_response(user_input: str, history: list[dict] | None = None) -> dict:
    if not API_KEY:
        raise ValueError("Missing MISTRAL_API_KEY. Set it in your environment or .env file.")

    classification_tmpl = load_text(PROMPTS_DIR / "classification.txt")
    issue_extraction_tmpl = load_text(PROMPTS_DIR / "issue_extraction.txt")
    feature_question_tmpl = load_text(PROMPTS_DIR / "feature_question.txt")
    system_question_tmpl = load_text(PROMPTS_DIR / "system_question.txt")
    general_question_tmpl = load_text(PROMPTS_DIR / "general_question.txt")

    kairos_info = load_text(DOCS_DIR / "kairos_info.txt")
    feature_breakdown = load_text(DOCS_DIR / "feature_breakdown.txt")
    system_archi = load_text(DOCS_DIR / "system_archiecture.txt")

    inquiry = build_inquiry(user_input, history)

    classification_prompt = classification_tmpl.format(inquiry=inquiry)
    intent = normalize_intent(mistral_chat(classification_prompt))

    issue_data = None
    summary = None
    explanation = None

    if intent == "Technical Issue":
        extraction_prompt = issue_extraction_tmpl.format(inquiry=inquiry)
        raw_json = mistral_chat(extraction_prompt)
        issue_data = sanitize_issue_data(extract_json(raw_json))

        system_context = f"{system_archi}\n\nObserved issue details:\n{json.dumps(issue_data, indent=2)}"
        system_prompt = system_question_tmpl.format(
            inquiry=inquiry,
            system_archi=system_context,
        )
        explanation = strip_markdown(mistral_chat(system_prompt))
        summary = summarize_issue(inquiry)

        details = json.dumps(issue_data, indent=2)
        response_text = (
            f"Summary: {summary}\n\n"
            f"{explanation}\n\n"
            "I've have saved your issue as this token:\n\n```json\n"
            f"{details}\n```"
        )
    elif intent == "Feature Explanation":
        prompt = feature_question_tmpl.format(
            inquiry=inquiry,
            feature_breakdown=feature_breakdown,
        )
        response_text = mistral_chat(prompt)
    elif intent == "System Architecture Explanation":
        prompt = system_question_tmpl.format(
            inquiry=inquiry,
            system_archi=system_archi,
        )
        response_text = mistral_chat(prompt)
    else:
        prompt = general_question_tmpl.format(
            inquiry=inquiry,
            kairos_info=kairos_info,
        )
        response_text = mistral_chat(prompt)

    response_text = strip_html_divs(response_text)

    return {
        "intent": intent,
        "summary": summary,
        "explanation": explanation,
        "issue_json": issue_data,
        "response": response_text,
    }
