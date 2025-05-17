import streamlit as st
import requests
import json
import time

st.header("💬 AI Chatbot App")

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
                    "Authorization": f"Bearer {st.secrets["OPEN_ROUTER_API_KEY"]}"
                },
                data=json.dumps({
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [user_payload],
                    "stream": True
                }),
                stream=True
            )
    #endregion

    if response is not None:
        empty_space.empty()

        # TODO : handle error message, need to use the status along with the error message aja
        if response.status_code == 200:
            full_response = ""
            with st.chat_message("assistant"):
                stream_placeholder = st.empty()
                # TODO : get method for stream_placeholder
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")

                        if decoded_line.startswith("data: "):
                            data = decoded_line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(data)
                                choices = json_data.get("choices")
                                if len(choices) > 0:
                                    delta = choices[0].get("delta")
                                    if "content" in delta:
                                        content = delta.get("content")
                                        full_response += content
                                        stream_placeholder.markdown(f"{full_response}▌")
                                        time.sleep(0.03)
                            except Exception as e:
                                st.error(f"Streaming error: {e}")

                stream_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
