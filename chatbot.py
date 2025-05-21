import datetime
import streamlit as st
from streamlit_javascript import st_javascript
import pytz
import requests
import json
import base64
import mimetypes
import uuid

# region Variables
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4.1"
ACCEPTED_FILE_TYPES = ["jpg", "jpeg", "png", "pdf"]

timezone = st_javascript("""await (async () => {
            const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            return userTimezone
})().then(returnValue => returnValue)""")
# endregion

if "messages" not in st.session_state:
    st.session_state.messages = []

# region Methods
def generate_assistant_response(response):
    # region Timestamp Information
    timestamp_placeholder = st.empty()
    name = "AI Assistant"
    user_tz = pytz.timezone(timezone)
    timestamp = datetime.datetime.now(user_tz)
    timestamp_placeholder.markdown(get_timestamp_string(name, timestamp))
    # endregion

    # region Message Information
    generated_response = ""
    message_placeholder = st.empty()
    message_placeholder.markdown("▌")
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
                        if is_list_not_empty(choices):
                            message_delta = choices[0].get("delta")
                            if "content" in message_delta:
                                generated_response += message_delta.get("content") or ""
                                message_placeholder.markdown(f"{generated_response}▌")
                except json.JSONDecodeError as ex:
                    display_error_message("**❌ Streaming Error:**", error_message=f"JSON decode error: {ex}")
                except KeyError as ex:
                    display_error_message("**❌ Streaming Error:**", error_message=f"Missing key: {ex}")
                except Exception as ex:
                    display_error_message("**❌ Streaming Error:**", error_message=str(ex))
    message_placeholder.markdown(generated_response)
    st.session_state.messages.append({"role": "assistant", "content": generated_response, "name": name, "timestamp": timestamp})
    # endregion

def display_error_message(error_title, error_subtitle = "", error_message = ""):
    msg = error_title
    if error_subtitle:
        msg += f"\n{error_subtitle}"
    if error_message:
        msg += f"\n{error_message}"
    st.error(msg)

def is_list_not_empty(list):
    return list is not None and len(list) > 0

def display_messages(text, files, name, timestamp):
    # region Timestamp Information
    st.markdown(get_timestamp_string(name, timestamp))
    # endregion

    # region Text Information
    if text:
        st.markdown(text)
    # endregion
    
    # region File Information
    if is_list_not_empty(files):
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
    # endregion

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
    if is_list_not_empty(files):
        for file in files:
            mime_type, _ = mimetypes.guess_type(file.name)
            
            # region Read and Encode Content to base64
            file_content = file.read()
            base64_data = base64.b64encode(file_content).decode("utf-8")
            file_data = f"data:{mime_type};base64,{base64_data}"
            file.seek(0)
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
    return {"Authorization": f"Bearer {st.secrets.get('OPEN_ROUTER_API_KEY')}"}

def get_input_data(input_content):
    user_message = { "role": "user", "content": input_content }
    return json.dumps({
        "model": MODEL,
        "messages": [user_message],
        "stream": True
    })

def styling_user_role():
    cssUserChat = """
    [class*="st-key-user"] .stChatMessage {
        flex-direction: row-reverse;
        text-align: right;
    }
    """
    st.markdown(f"<style>{cssUserChat}</style>", unsafe_allow_html=True)

def get_timestamp_string(name, timestamp):
    return f"**{name} - {timestamp.strftime('%A, %d %B %Y %H.%M.%S %Z')}**"

def get_role_avatar(role):
    return "assets/user.png" if role == "user" else "assets/ai_assistant.png"
# endregion

st.header("💬 AI Chatbot App")
st.markdown(f"Powered by ```{MODEL}``` via OpenRouter 👾")
st.markdown("Accepted file types to be uploaded: ```JPG```, ```JPEG```, ```PNG```, ```PDF``` and we can upload multiple files.")

# region Displayed Messages
for message in st.session_state.messages:
    role = message.get("role")
    with st.container(key=f"{role}-{str(uuid.uuid4())}"):
        with st.chat_message(role, avatar=get_role_avatar(role)):
            display_messages(message.get("content"), message.get("files", []), message.get("name"), message.get("timestamp"))
# endregion

# region Styling the "User" role chat component into the right side
styling_user_role()
# endregion

user_input = st.chat_input("Input your message here", accept_file="multiple", file_type=["jpg", "jpeg", "png", "pdf"])

if user_input is not None:
    text = user_input.get("text")
    files = user_input.get("files", [])

    if not text and not files:
        # Happens when we tried to send the message, specifically when we uploaded invalid file type from drag and drop as Streamlit filters out invalid file types.
        display_error_message("**❌ Error**", error_message="Please enter a message or upload a file before sending.")
    else:
        input_content = get_input_content(text, files)

        name = "User"
        user_tz = pytz.timezone(timezone)
        timestamp = datetime.datetime.now(user_tz)

        role = "user"
        with st.container(key=f"{role}-{str(uuid.uuid4())}"):
            with st.chat_message(role, avatar=get_role_avatar(role)):
                display_messages(text, files, name, timestamp)
        
        st.session_state.messages.append({
            "role": role,
            "content": text,
            "files": files,
            "name": name,
            "timestamp": timestamp
        })

        # region Create a request to the server
        exception_occurred = False
        error_message = ""
        response = None

        empty_space = st.empty()
        with empty_space.container():
            with st.status("Please wait, the AI assistant is typing a message...", expanded=True):
                try:
                    response = requests.post(
                        url=BASE_URL,
                        headers=get_input_headers(),
                        data=get_input_data(input_content),
                        stream=True,
                        timeout=30
                    )
                except requests.Timeout:
                    exception_occurred = True
                    error_message = "Request timed out. Please try again."
                except requests.RequestException as e:
                    exception_occurred = True
                    error_message = str(e)
        # endregion

        # region Retrieve a response
        if exception_occurred:
            empty_space.empty() # Hide Loading Component
            display_error_message("**❌ Error**", error_message=error_message)
        elif response is not None:
            empty_space.empty() # Hide Loading Component

            if response.status_code == 200:
                # region Show Success Response from Assistant
                role = "assistant"
                with st.container(key=f"{role}-{str(uuid.uuid4())}"):
                    with st.chat_message(role, avatar=get_role_avatar(role)):
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
        else:
            empty_space.empty() # Hide Loading Component
        # endregion