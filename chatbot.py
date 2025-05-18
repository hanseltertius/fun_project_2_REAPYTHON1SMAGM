import streamlit as st
import requests
import json
import base64
import mimetypes
import uuid

st.header("💬 AI Chatbot App")
st.markdown("Powered by ```google/gemini-2.5-flash-preview``` via OpenRouter 👾")

# region Methods
def generate_assistant_response(response):
    stream_placeholder = st.empty()
    generated_response = ""
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")

            if decoded_line.startswith("data: "):
                data = decoded_line[6:]
                if data == "[DONE]":
                    break
                try:
                    json_data = json.loads(data)
                    error = json_data.get("error")
                    if error is not None:
                        display_error_message("**❌ Error:**", error_message=error.get("message"))
                    else:
                        choices = json_data.get("choices")
                        if check_list_not_empty(choices):
                            message_delta = choices[0].get("delta")
                            if "content" in message_delta:
                                generated_response += message_delta.get("content") or ""
                                stream_placeholder.markdown(f"{generated_response}▌")
                except Exception as ex:
                    display_error_message("**❌ Streaming Error:**", error_message=ex)
    stream_placeholder.markdown(generated_response)
    st.session_state.messages.append({"role": "assistant", "content": generated_response})

def display_error_message(error_title, error_subtitle = "", error_message = ""):
    st.error(f"""
        {error_title}\n
        {f"{error_subtitle}\n" if error_subtitle else ""}
        {f"{error_message}\n" if error_message else ""}
    """)

def check_list_not_empty(list):
    return list is not None and len(list) > 0

def get_displayed_messages(text, files):
    st.markdown(text)
    if check_list_not_empty(files):
        for file in files:
            mime_type, _ = mimetypes.guess_type(file.name)
            if mime_type == "application/pdf":
                st.download_button(
                    label=f"📄 Download {file.name}",
                    data=file,
                    file_name=file.name,
                    mime=mime_type,
                    key=str(uuid.uuid4())
                )
            else:
                st.image(file)

def get_input_content(text, files):
    input_content = []

    # region Add Text to input
    if text:
        input_content.append({
            "type": "text",
            "text": text
        })
    # endregion

    # region Add File to input
    if check_list_not_empty(files):
        for file in files:
            mime_type, _ = mimetypes.guess_type(file.name)
            
            # region Read and Encode Content to base64
            file_content = file.read()
            base64_data = base64.b64encode(file_content).decode("utf-8")
            file_data = f"data:{mime_type};base64,{base64_data}"
            # endregion

            if mime_type == "application/pdf":
                input_content.append({
                    "type": "file",
                    "file": {
                        "filename": file.name,
                        "file_data": file_data
                    }
                })
            else:
                input_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": file_data
                    }
                })
    # endregion

    return input_content
    
def get_input_headers():
    return {"Authorization": f"Bearer {st.secrets.get("OPEN_ROUTER_API_KEY")}"}

def get_input_data(input_content):
    user_message = { "role": "user", "content": input_content }
    return json.dumps({
        "model": "google/gemini-2.5-flash-preview",
        "messages": [user_message],
        "stream": True
    })
# endregion

if "messages" not in st.session_state:
    st.session_state.messages = []

# region Displayed Messages
for message in st.session_state.messages:
    with st.chat_message(message.get("role")):
        get_displayed_messages(message.get("content"), message.get("files"))
# endregion

user_input = st.chat_input("Input your message here", accept_file="multiple", file_type=["jpg", "jpeg", "png", "pdf"])

if user_input is not None:
    text = user_input.get("text")
    files = user_input.get("files")
    input_content = get_input_content(text, files)

    with st.chat_message("user"):
        get_displayed_messages(text, files)
    
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
                headers=get_input_headers(),
                data=get_input_data(input_content),
                stream=True
            )
    #endregion

    if response is not None:
        empty_space.empty() # Hide Loading Component

        if response.status_code == 200:
            # region Show Success Response from Assistant
            with st.chat_message("assistant"):
                generate_assistant_response(response)
            # endregion
        else:
            # region Show Error Response when status code retrieved from API is not succeed
            error_json = json.loads(response.text)
            error = error_json.get("error")
            error_message = error.get("message")
            error_status_code = error.get("code")
            display_error_message("**❌ Error**", f"**Status Code:** {error_status_code}", error_message)
            # endregion
