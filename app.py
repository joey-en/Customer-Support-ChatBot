import html
import re

import streamlit as st

from core import generate_response

# Page config
st.set_page_config(page_title="Kairos Chatbot", page_icon="🎞️", layout="wide")


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
st.markdown(
    "Kairos is an AI-powered long-form video understanding and retrieval platform "
    "that turns long videos into searchable, conversationally accessible content, created for our capstone."
)

st.markdown(
    "‼️THIS IS NOT THE KAIROS PROJECT ‼️"
)
    
st.markdown(
    "I just didn't know what to make a chatbot of so I imagined a Kairos customer support chatbot."
)

# Chat container
chat_container = st.container()

# Input form
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message...")
    submitted = st.form_submit_button("Send")

    if submitted and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        try:
            result = generate_response(user_input, history=st.session_state.messages[:-1])
            assistant_response = result["response"]
        except ValueError as exc:
            assistant_response = str(exc)

        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Render chat messages
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            assistant_html = render_assistant_html(msg["content"])
            st.markdown(f"<div class='assistant'>{assistant_html}</div>", unsafe_allow_html=True)
