import streamlit as st
import requests
import json

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

    # TODO : simpan chat history untuk si user message

    user_payload = {
        "role": "user",
        "content": message_input
    }

    with st.chat_message(user_payload.get("role")):
        st.markdown(user_payload.get("content"))

    st.session_state.messages.append(user_payload)

    #region Generating the Loading Component
    empty_space = st.empty()
    with empty_space.container():
        with st.status("Please wait, the AI assistant is tying a message...", expanded=True):
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer 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"
                },
                data=json.dumps({
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [user_payload]
                })
            )
    #endregion

    if response:
        empty_space.empty()

        # TODO : handle error message, need to use the status along with the error message aja
        if response.status_code == 200:
            response_text_object = json.loads(response.text)

            text_message_choices = response_text_object.get("choices")
            if len(text_message_choices) > 0:
                message_output = text_message_choices[0].get("message")
                message_output_role = message_output.get("role")
                message_output_content = message_output.get("content")

                # TODO : use yield, seperti di ChatGPT
                with st.chat_message(message_output_role):
                    st.markdown(message_output_content)

                st.session_state.messages.append({"role": message_output_role, "content": message_output_content})
