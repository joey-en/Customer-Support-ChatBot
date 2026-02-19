import html
import json
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from mistralai import Mistral, UserMessage

# Page config
st.set_page_config(page_title="Kairos Chatbot", page_icon="🎞️", layout="wide")

# Env + model config
load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
DOCS_DIR = BASE_DIR / "documents"


@st.cache_data
def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_inquiry(user_input: str, history: list[dict]) -> str:
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


def render_assistant_html(content: str) -> str:
    parts = []
    pattern = re.compile(r"```(?:\w+)?\n(.*?)\n```", re.DOTALL)
    last = 0
    for match in pattern.finditer(content):
        start, end = match.span()
        text_chunk = content[last:start]
        if text_chunk:
            parts.append(html.escape(text_chunk).replace("\n", "<br>"))
        code = html.escape(match.group(1))
        parts.append(f"<pre><code>{code}</code></pre>")
        last = end
    tail = content[last:]
    if tail:
        parts.append(html.escape(tail).replace("\n", "<br>"))
    return "".join(parts)


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

# Initialize session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if not st.session_state.messages:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "Hi there! How can I help you today? I'm your Kairos customer support assistant.",
        }
    )

# CSS for chat bubbles
st.markdown(
    """
<style>
.assistant {
    background-color: #28174f;
    color: white;
    padding: 10px 15px;
    border-radius: 20px;
    margin: 5px 0px;
    width: fit-content;
    max-width: 70%;
    align-self: flex-end;
}
.user {
    background-color: #E0E0E0;
    color: #0E2345;
    padding: 10px 15px;
    border-radius: 20px;
    margin-left: auto;
    width: fit-content;
    max-width: 70%;
    align-self: flex-end;
}
.chat-container {
    display: flex;
    flex-direction: column;
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("🎞️ Kairos Support Chatbot")

# Chat container
chat_container = st.container()

# Input form
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message...")
    submitted = st.form_submit_button("Send")

    if submitted and user_input:
        if not API_KEY:
            st.error("Missing MISTRAL_API_KEY. Set it in your environment or .env file.")
            st.stop()

        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Load prompt templates and documents
        classification_tmpl = load_text(PROMPTS_DIR / "classification.txt")
        issue_extraction_tmpl = load_text(PROMPTS_DIR / "issue_extraction.txt")
        feature_question_tmpl = load_text(PROMPTS_DIR / "feature_question.txt")
        system_question_tmpl = load_text(PROMPTS_DIR / "system_question.txt")
        general_question_tmpl = load_text(PROMPTS_DIR / "general_question.txt")

        kairos_info = load_text(DOCS_DIR / "kairos_info.txt")
        feature_breakdown = load_text(DOCS_DIR / "feature_breakdown.txt")
        system_archi = load_text(DOCS_DIR / "system_archiecture.txt")

        inquiry = build_inquiry(user_input, st.session_state.messages[:-1])

        # classification
        classification_prompt = classification_tmpl.format(inquiry=inquiry)
        intent = normalize_intent(mistral_chat(classification_prompt))

        # conditional extraction + response
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
            assistant_response = (
                f"Summary: {summary}\n\n"
                f"{explanation}\n\n"
                "I've logged the issue. Details:\n\n```json\n"
                f"{details}\n```"
            )
        elif intent == "Feature Explanation":
            prompt = feature_question_tmpl.format(
                inquiry=inquiry,
                feature_breakdown=feature_breakdown,
            )
            assistant_response = mistral_chat(prompt)
        elif intent == "System Architecture Explanation":
            prompt = system_question_tmpl.format(
                inquiry=inquiry,
                system_archi=system_archi,
            )
            assistant_response = mistral_chat(prompt)
        else:
            prompt = general_question_tmpl.format(
                inquiry=inquiry,
                kairos_info=kairos_info,
            )
            assistant_response = mistral_chat(prompt)

        assistant_response = strip_html_divs(assistant_response)
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Render chat messages
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            assistant_html = render_assistant_html(msg["content"])
            st.markdown(f"<div class='assistant'>{assistant_html}</div>", unsafe_allow_html=True)
