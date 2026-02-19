import streamlit as st

# Page config
st.set_page_config(page_title="Kairos Chatbot", page_icon="🎥", layout="wide")

# Initialize session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []

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

st.title("🎥 Kairos Support Chatbot")

# Chat container
chat_container = st.container()

# Input form
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message...")
    submitted = st.form_submit_button("Send")

    if submitted and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Placeholder assistant response (replace with backend call later)
        assistant_response = f"Assistant reply to: '{user_input}'"
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Render chat messages
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant'>{msg['content']}</div>", unsafe_allow_html=True)

