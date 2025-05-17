import streamlit as st

st.header("💬 AI Chatbot App")

# TODO : generate the echo, it is to test the robot's response

if "messages" not in st.session_state:
    st.session_state.messages = []

# region Displayed Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# endregion

if message_input := st.chat_input("Input your message here"):

    # TODO : need to check if the response is 200 first ya
    with st.chat_message("user"):
        st.markdown(message_input)
    # TODO : only call when the response is 200, need to input first into the OpenRouter API
    user_payload = {
        "role": "user",
        "content": message_input
    }
    st.session_state.messages.append(user_payload)

    message_response = f"Echo: {message_input}"
    with st.chat_message("assistant"):
        st.markdown(message_response)
    st.session_state.messages.append({"role": "assistant", "content": message_response})
