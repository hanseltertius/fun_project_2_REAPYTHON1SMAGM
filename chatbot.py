import streamlit as st
import requests
import json
import base64
import mimetypes

st.header("💬 AI Chatbot App")

# region Methods
def get_generated_response(response):
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
                        display_error_message("**❌ Error:**", f"{error.get("message")}")
                    else:
                        choices = json_data.get("choices")
                        if choices is not None and len(choices) > 0:
                            delta = choices[0].get("delta")
                            if "content" in delta:
                                content = delta.get("content")
                                generated_response += content
                                stream_placeholder.markdown(f"{generated_response}▌")
                except Exception as e:
                    display_error_message("**❌ Streaming Error:**", f"{e}")
    stream_placeholder.markdown(generated_response)
    return generated_response

def display_error_message(error_title, error_message, error_subtitle = ""):
    subtitle = f"{error_subtitle}\n" if error_subtitle else ""
    st.error(f"""
        {error_title}\n
        {subtitle}
        {error_message}
    """)

def check_files_not_empty(files):
    return files is not None and len(files) > 0

def get_displayed_messages(text, files):
    st.markdown(text)
    if check_files_not_empty(files):
        for file in files:
            st.image(file)

def get_input_content(text, files):
    input_content = []

    if text:
        input_content.append({
            "type": "text",
            "text": text
        })

    if check_files_not_empty(files):
        for file in files:
            # Determine the MIME type of the uploaded file
            mime_type, _ = mimetypes.guess_type(file.name)
            
            # Read and encode the file content to base64
            file_content = file.read()
            base64_data = base64.b64encode(file_content).decode("utf-8")
            data_url = f"data:{mime_type};base64,{base64_data}"

            input_content.append({
                "type": "image_url",
                "image_url": {
                    "url": data_url
                }
            })

    return input_content
    
def get_input_headers():
    return {"Authorization": f"Bearer {st.secrets["OPEN_ROUTER_API_KEY"]}"}

def get_input_data(input_content):
    payload = { "role": "user", "content": input_content }
    return json.dumps({
        "model": "google/gemini-2.5-flash-preview",
        "messages": [payload],
        "stream": True
    })
# endregion

if "messages" not in st.session_state:
    st.session_state.messages = []

# region Displayed Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        get_displayed_messages(message.get("content"), message.get("files"))
# endregion

user_input = st.chat_input("Input your message here", accept_file="multiple", file_type=["jpg", "jpeg", "png"])

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
        empty_space.empty()

        if response.status_code == 200:
            with st.chat_message("assistant"):
                generated_response = get_generated_response(response)
                st.session_state.messages.append({"role": "assistant", "content": generated_response})
        else:
            error_json = json.loads(response.text)
            error = error_json.get("error")
            error_message = error.get("message")
            error_status_code = error.get("code")
            display_error_message("**❌ Error**", error_message, f"**Status Code:** {error_status_code}")
