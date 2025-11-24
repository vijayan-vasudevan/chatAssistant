import streamlit as st
import sys
import os
import warnings


# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordinatoragent.main import get_response
from agents.coordinatoragent.main import ingest_data_from_docs
from agents.coordinatoragent.models.coordinator_agent_request import CoordinatorAgentRequest

warnings.filterwarnings("ignore")
# -------------------- Configuration --------------------
st.set_page_config(page_title="💬 EduTrack", page_icon="🧠", layout="centered")

# -------------------- Streamlit UI --------------------
st.title("🤖 EduTrack Chat Assistant Agent")
st.markdown("Type below to chat with EduTrack Chat Assistant Agent!")

# Use Streamlit session state to store chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    ingest_data_from_docs()

if "user_id" not in st.session_state:
    # For local testing used hard-coded value
    st.session_state.user_id = "a8e25c9f-aabd-4b04-969e-af2e9bbaa032"
    # st.session_state.user_id = str(uuid.uuid4())

# Text input box
user_input = st.text_input("You:", placeholder="Ask me anything related to EduTrack...", key="input_box")

# When user submits a message
if user_input:
    with st.spinner("Thinking..."):
        response = get_response(CoordinatorAgentRequest(user_input=user_input, user_id=st.session_state.user_id))

    # Append to history
    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("Bot", response))

# Display chat history
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"🧑 **{sender}:** {message}")
    else:
        st.markdown(f"🤖 **{sender}:** {message}")