import streamlit as st
import requests
import json
import time
import base64
import mimetypes

st.header("💬 AI Chatbot App")

if "messages" not in st.session_state:
    st.session_state.messages = []

# region Displayed Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "files" in message and message["files"]:
            for img in message["files"]:
                st.image(img)
# endregion

user_input = st.chat_input("Input your message here", accept_file="multiple", file_type=["jpg", "jpeg", "png"])

if user_input is not None:
    text = user_input.get("text")
    files = user_input.get("files")
    messages = []

    if text:
        messages.append({
            "type": "text",
            "text": text
        })

    # TODO : make a reusable function to get if the files list is not empty
    if files is not None and len(files) > 0:
        for file in files:
            # Determine the MIME type of the uploaded file
            mime_type, _ = mimetypes.guess_type(file.name)
            
            # Read and encode the file content to base64
            file_content = file.read()
            base64_data = base64.b64encode(file_content).decode("utf-8")
            data_url = f"data:{mime_type};base64,{base64_data}"

            messages.append({
                "type": "image_url",
                "image_url": {
                    "url": data_url
                }
            })

    user_payload = {
        "role": "user",
        "content": messages
    }

    with st.chat_message("user"):
        st.markdown(text)
        if files is not None and len(files) > 0:
            for file in files:
                st.image(file)
    
    st.session_state.messages.append({
        "role": "user",
        "content": text,
        "files": files
    })

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
                    "model": "google/gemini-2.5-flash-preview",
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
                # TODO : get method for full_response
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")

                        if decoded_line.startswith("data: "):
                            data = decoded_line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(data)
                                # TODO : get error atau tidak, ini untuk error handling nya bagaimana
                                error = json_data.get("error")
                                if error is not None:
                                    st.error(f"""
                                    **❌ Error:**\n
                                    {error.get("message")}
                                    """)
                                else:
                                    choices = json_data.get("choices")
                                    if choices is not None and len(choices) > 0:
                                        delta = choices[0].get("delta")
                                        if "content" in delta:
                                            content = delta.get("content")
                                            full_response += content
                                            stream_placeholder.markdown(f"{full_response}▌")
                                            time.sleep(0.03)
                            except Exception as e:
                                st.error(f"""
                                **❌ Streaming Error:**\n
                                {e}
                                """)

                stream_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            error_json = json.loads(response.text)
            error = error_json.get("error")
            error_message = error.get("message")
            error_status_code = error.get("code")
            st.error(f"""
            **❌ Error**\n
            **Status Code:** {error_status_code}\n
            {error_message}
            """)
