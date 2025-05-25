import datetime
import streamlit as st
from streamlit_javascript import st_javascript
import pytz
import requests
import json
import base64
import mimetypes
import uuid
import io
from db.chat_history import init_db, save_message_into_session, fetch_chat_history, create_session, get_sessions, delete_all_sessions

# region Variables
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4.1"
ACCEPTED_FILE_TYPES = ["jpg", "jpeg", "png", "pdf"]
USER = "user"
ASSISTANT = "assistant"

timezone = st_javascript("""await (async () => {
            const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            return userTimezone
})().then(returnValue => returnValue)""")
# endregion

# region State Initialization
def initialize_session_state():
    defaults = {
        "new_session": False,
        "messages": [],
        "create_new_session_error_message": "",
        "session_name_error": False,
        "session_changed": False,
        "generating_response": False,
        "input_error_message": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Call this function at the top of your script
initialize_session_state()
# endregion

# region Methods
def get_timestamp():
    user_tz = pytz.timezone(timezone)
    return datetime.datetime.now(user_tz).isoformat()

def generate_assistant_response(response):
    # region Timestamp Information
    timestamp_placeholder = st.empty()
    name = "AI Assistant"
    timestamp = get_timestamp()
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
                        st.session_state.generating_response = False
                        st.session_state.input_error_message = {
                            "title": "**❌ Error**",
                            "subtitle": "",
                            "message": "Please enter a message or upload a file before sending."
                        }
                        st.rerun()
                    else:
                        choices = json_data.get("choices")
                        if is_list_not_empty(choices):
                            message_delta = choices[0].get("delta")
                            if "content" in message_delta:
                                generated_response += message_delta.get("content") or ""
                                message_placeholder.markdown(f"{generated_response}▌")
                except json.JSONDecodeError as ex:
                    st.session_state.generating_response = False
                    st.session_state.input_error_message = {
                        "title": "**❌ Streaming Error**",
                        "subtitle": "",
                        "message": f"JSON decode error: {ex}"
                    }
                    st.rerun()
                except KeyError as ex:
                    st.session_state.generating_response = False
                    st.session_state.input_error_message = {
                        "title": "**❌ Streaming Error**",
                        "subtitle": "",
                        "message": f"Missing key: {ex}"
                    }
                    st.rerun()
                except Exception as ex:
                    st.session_state.generating_response = False
                    st.session_state.input_error_message = {
                        "title": "**❌ Streaming Error**",
                        "subtitle": "",
                        "message": str(ex)
                    }
                    st.rerun()
    message_placeholder.markdown(generated_response)
    st.session_state.messages.append({"role": ASSISTANT, "content": generated_response, "name": name, "timestamp": timestamp})
    save_message_into_session(session_id, ASSISTANT, name, generated_response, timestamp)
    # endregion

def display_error_message(error_title, error_subtitle = "", error_message = ""):
    st.error(f"""
        {error_title}
        {error_subtitle}
        {error_message}
    """)

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
        display_files(files)
    # endregion

def display_files(files):
    for file in files:
        if isinstance(file, dict):
            # region If file is from DB / history
            filename = file.get("name")
            mimetype = file.get("mimetype")
            data = file.get("data")
            if mimetype and mimetype.startswith("image/"):
                img_bytes = base64.b64decode(data)
                st.image(io.BytesIO(img_bytes), caption=filename)
            else:
                st.download_button(
                    label=f"Download {filename}",
                    data=base64.b64decode(data),
                    file_name=filename,
                    mime=mimetype,
                    key=str(uuid.uuid4())
                )
            # endregion
        else:
            # region If file is from File Upload
            filename = file.name
            mimetype = file.type
            file_data = file.getvalue()
            if mimetype and mimetype.startswith("image/"):
                st.image(io.BytesIO(file_data), caption=filename)
            else:
                st.download_button(
                    label=f"Download {filename}",
                    data=file_data,
                    file_name=filename,
                    mime=mimetype,
                    key=str(uuid.uuid4())
                )
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
    user_message = { "role": USER, "content": input_content }
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

def format_timestamp(timestamp):
    if isinstance(timestamp, str):
        # Parse ISO string to datetime object
        timestamp = datetime.datetime.fromisoformat(timestamp)
    return timestamp.strftime('%A, %d %B %Y %H.%M.%S %Z')

def get_timestamp_string(name, timestamp):
    return f"**{name} - {format_timestamp(timestamp)}**"

def get_role_avatar(role):
    return "assets/user.png" if role == USER else "assets/ai_assistant.png"

def generate_chat_input(text, files):
    name = "User"
    role = USER
    input_content = get_input_content(text, files)
    timestamp = get_timestamp()

    with st.container(key=f"{role}-{str(uuid.uuid4())}"):
        with st.chat_message(role, avatar=get_role_avatar(role)):
            display_messages(text, files, name, timestamp)
    
    st.session_state.messages.append({
        "role": role,
        "content": text,
        "files": [
            {
                "name": file.name,
                "mimetype": file.type,
                "data": base64.b64encode(file.getvalue()).decode("utf-8")
            } for file in files
        ] if files else [],
        "name": name,
        "timestamp": timestamp
    })
    save_message_into_session(session_id, USER, name, text, timestamp, files)

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
        st.session_state.generating_response = False
        st.session_state.input_error_message = {
            "title": "**❌ Error**",
            "subtitle": "",
            "message": error_message
        }
        st.rerun()
    elif response is not None:
        empty_space.empty() # Hide Loading Component

        if response.status_code == 200:
            # region Show Success Response from Assistant
            role = ASSISTANT
            with st.container(key=f"{role}-{str(uuid.uuid4())}"):
                with st.chat_message(role, avatar=get_role_avatar(role)):
                    generate_assistant_response(response)
                    st.session_state.generating_response = False
                    st.rerun() # Rerun to reset the state of new session creation
            # endregion
        else:
            # region Show Error Response when status code retrieved from API is not succeed
            error_json = json.loads(response.text)
            error = error_json.get("error")
            error_message = error.get("message")
            error_status_code = error.get("code")
            
            st.session_state.generating_response = False
            st.session_state.input_error_message = {
                "title": "**❌ Error**",
                "subtitle": f"**Status Code:** {error_status_code}",
                "message": error_message
            }
            st.rerun()
            # endregion
    else:
        empty_space.empty() # Hide Loading Component
        st.session_state.generating_response = False
        st.rerun()
    # endregion

def on_session_change():
    st.session_state.session_changed = True

def on_session_name_input_change():
    st.session_state.add_new_session_error_message = ""
    st.session_state.session_name_error = False

def on_submit_chat_input():
    st.session_state.generating_response = True
    st.session_state.input_error_message = {}

@st.dialog("Confirm to Delete")
def show_delete_confirmation():
    st.write("Are you sure you want to delete all sessions? This action cannot be undone.")
    if st.button("Yes, delete all sessions", use_container_width=True):
        delete_all_sessions()
        st.session_state.new_session = True
        st.session_state.create_new_session_error_message = ""
        st.session_state.session_name_error = False
        st.rerun()

def on_create_session(new_session_name, is_input_chat=False, text=None, files=None):
    if new_session_name:
        if new_session_name in session_names:
            # region Check if session name already exists
            st.session_state.create_new_session_error_message = "Session name already exists. Please choose a different name."
            st.session_state.session_name_error = True
            st.session_state.generating_response = False
            st.rerun()
            # endregion
        else:
            # region Create a new session
            session_id = create_session(new_session_name, get_timestamp())
            st.session_state.create_new_session_error_message = ""
            st.session_state.session_id = session_id
            st.session_state.session_name_error = False
            
            if is_input_chat:
                # region Sending messages
                st.session_state.messages = []
                st.session_state.pending_message = {
                    "text": text,
                    "files": files
                }
                # endregion
            
            st.session_state.new_session = False
            st.rerun()
            # endregion
    else:
        # region Error message for empty session input name
        st.session_state.create_new_session_error_message = "Session name must not be empty."
        st.session_state.session_name_error = True
        st.session_state.generating_response = False
        st.rerun()
        # endregion
# endregion

# region Sidebar
# region Session Selection / Creation
init_db()
sessions = get_sessions()
session_names = [name for (_, name) in sessions]
session_ids = [sid for (sid, _) in sessions]

# region Sidebar Header
st.sidebar.title("💬 AI Chatbot App")
st.sidebar.markdown(f"Powered by ```{MODEL}``` via OpenRouter 👾")
st.sidebar.markdown("Accepted file types to be uploaded: ```JPG```, ```JPEG```, ```PNG```, ```PDF``` and we can upload multiple files.")
# endregion

# region Sidebar Session
st.sidebar.subheader("Chat Sessions")

# region Sidebar Layout
if st.session_state.new_session:
    if is_list_not_empty(sessions):
        if st.sidebar.button(
            "⬅️ Back", 
            key="back_to_sessions", 
            use_container_width=True,
            disabled=st.session_state.get("generating_response", False)
        ):
            st.session_state.new_session = False
            st.session_state.create_new_session_error_message = ""
            st.session_state.session_name_error = False
            st.rerun()

    new_session_name = st.sidebar.text_input(
        "Session name", 
        key="new_session_name", 
        on_change=on_session_name_input_change, 
        placeholder="Input session name here (enter message to create a new session)"
    )

    if st.session_state.session_name_error:
        st.sidebar.error(st.session_state.create_new_session_error_message)
else:
    if st.sidebar.button(
        "➕ New Session", 
        use_container_width=True,
        disabled=st.session_state.get("generating_response", False)
    ):
        st.session_state.new_session = True
        st.session_state.create_new_session_error_message = ""
        st.session_state.session_name_error = False
        st.rerun()

    if st.sidebar.button(
        "🗑️ Delete all sessions",
        use_container_width=True,
        disabled=st.session_state.get("generating_response", False)
    ):
        show_delete_confirmation()

    selected_idx = st.sidebar.radio(
        "Select a session",
        options=list(range(len(session_names))),
        format_func=lambda i: session_names[i],
        index=session_ids.index(st.session_state.get("session_id", session_ids[0])) if session_ids else 0,
        key="session_radio",
        on_change=on_session_change,
        disabled=st.session_state.get("generating_response", False)
    )
    # region Handle Session Selection Change from Radio Button
    st.session_state.session_id = session_ids[selected_idx]
    if st.session_state.get("session_changed"):
        st.session_state.session_changed = False
        st.rerun()
    # endregion

# endregion

# region Initialize Session Data
if is_list_not_empty(sessions):
    # set selected session ID based on the initial value of Radio Button
    if not st.session_state.new_session:
        st.session_state.session_id = session_ids[0]
else:
    st.session_state.new_session = True
# endregion

# region Load messages for the current session
session_id = st.session_state.get("session_id")
if session_id:
    st.session_state.messages = fetch_chat_history(session_id)
else:
    st.session_state.messages = []
# endregion

# endregion

# region Main Chat UI

# region Styling the "User" role chat component into the right side
styling_user_role()
# endregion

# region State Initialization after re-rendering

# region Displayed Messages
for message in st.session_state.messages:
    role = message.get("role")
    with st.container(key=f"{role}-{str(uuid.uuid4())}"):
        with st.chat_message(role, avatar=get_role_avatar(role)):
            display_messages(message.get("content"), message.get("files", []), message.get("name"), message.get("timestamp"))
# endregion

# region Handle Pending Message from sending a message while creating a new session
if "pending_message" in st.session_state:
    pending = st.session_state.pop("pending_message", None)
    if pending:
        generate_chat_input(pending.get("text", ""), pending.get("files", []))
# endregion

if "input_error_message" in st.session_state and st.session_state.input_error_message:
    input_error = st.session_state.input_error_message
    display_error_message(input_error.get("title", ""), input_error.get("subtitle", ""), input_error.get("message", ""))
# endregion

user_input = st.chat_input(
    "Input your message here", 
    accept_file="multiple", 
    file_type=ACCEPTED_FILE_TYPES,
    disabled=st.session_state.get("generating_response", False),
    on_submit=on_submit_chat_input
)

if user_input is not None:
    text = user_input.get("text")
    files = user_input.get("files", [])

    if not text and not files:
        # Happens when we tried to send the message, specifically when we uploaded invalid file type from drag and drop as Streamlit filters out invalid file types.
        st.session_state.generating_response = False
        st.session_state.input_error_message = {
            "title": "**❌ Error**",
            "subtitle": "",
            "message": "Please enter a message or upload a file before sending."
        }
        st.rerun()
    else:
        if st.session_state.new_session:
            # region Handle New Session Creation on chat input
            new_session_name = st.session_state.get("new_session_name")
            on_create_session(new_session_name, is_input_chat=True, text=text, files=files)
            # endregion
        else:
            st.session_state.pending_message = {"text": text, "files": files}
            st.rerun()
# endregion