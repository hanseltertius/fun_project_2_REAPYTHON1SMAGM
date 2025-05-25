# fun_project_2_REAPYTHON1SMAGM

### Table of Contents

- [fun\_project\_2\_REAPYTHON1SMAGM](#fun_project_2_reapython1smagm)
    - [Table of Contents](#table-of-contents)
    - [Project Description](#project-description)
    - [How to Setup Project](#how-to-setup-project)
    - [How to Obtain OpenRouter API Key](#how-to-obtain-openrouter-api-key)
    - [Usage](#usage)
    - [Features](#features)
    - [Demo](#demo)
      - [Send a text](#send-a-text)
      - [Send an image](#send-an-image)
      - [Send a PDF File](#send-a-pdf-file)
      - [Session Validation](#session-validation)
        - [Empty Session](#empty-session)
        - [Duplicate Session](#duplicate-session)
      - [Delete All Sessions](#delete-all-sessions)

### Project Description

This project is to create a chatbot app that can send any kind of text, images
as well as PDF Document powered by `openai/gpt-4.1`

This project is a part of Ruangguru Skill Academy Python AI Bootcamp Batch 1.

For more info about Ruangguru Skill Python Academy Bootcamp can check out in
here: [Python AI Bootcamp by Ruangguru](https://rea.ruangguru.com/python-ai)

### How to Setup Project

1. Clone the Repository
   - `git clone https://github.com/hanseltertius/fun_project_2_REAPYTHON1SMAGM.git`
2. Create Virtual Environment in Python
   - `python -m venv myenv`
   - To activate the virtual environment, we need to type:
     - If using Windows : `myenv\Scripts\activate`
     - If using Mac : `source myenv/bin/activate`
3. Install some libraries (only if those libraries does not installed globally):
   - `pip install streamlit streamlit-javascript`
4. We need to [create a OpenRouter API Key](#how-to-obtain-openrouter-api-key)
   into the secrets file.

### How to Obtain OpenRouter API Key

1. Try to login with OpenRouter Account
   - If you don't have the account, we need to sign up in
     [here.](https://openrouter.ai/sign-up)
2. After Login / Sign Up, we need to go to the API Keys in the Dashboard
   - Click "API Keys" menu
   - Click "Create API Key" button
     ![Screenshot](screenshots/Menu%20API%20Key.png)
   - Fill in the Name -> Click "Create" button
     ![Screenshot](screenshots/Create%20a%20Key.png)
3. After create API Key, click "Copy" button
   ![Screenshot](screenshots/Copy%20a%20Token.png)
4. We need to implement OpenRouter API Key in the local
   - Create .streamlit folder
   - Create secrets.toml file inside the folder
     ![Screenshot](screenshots/Define%20the%20Token.png)

### Usage

In order to run the project locally, we need to type:

- `streamlit run app.py`
- Click the link in the Local URL part
  ![Screenshot](screenshots/Running%20the%20project%20in%20localhost.png)

If not in local, we can use:

- [Chatbot Fun Project 2](https://chatbot-fun-project.streamlit.app/)

### Features

In this project, the features include:

- Input text into chat
- Ability to upload file(s):
  - Upload Images in .jpg, .jpeg, .png file format
  - Upload PDF File

### Demo

#### Send a text

![Screenshot](screenshots/Input%20Text.png)

- Click **"Send (>) Button"** (only works when the text is not empty)
- While we try to add session, where the text input involves entering session
  name, entering the chat will create a new session

![Screenshot](screenshots/Input%20Text%20Result.png)

- The AI Assistant are able to generate the suitable response

#### Send an image

![Screenshot](screenshots/Upload%20Image%20Text.png)

- We clicked the **"Attachment Icon"** button to be able to upload image (accept
  only .jpg, .jpeg, .png)

![Screenshot](screenshots/Upload%20Image%20Result.png)

![Screenshot](screenshots/Upload%20Image%20Result%202.png)

- The AI Assistant will generate the response based on uploaded image

#### Send a PDF File

![Screenshot](screenshots/Upload%20PDF%20Text.png)

- Click the **"Attachment Icon"** button to upload a PDF document.

![Screenshot](screenshots/Upload%20PDF%20Result.png)

- The AI Assistant will generate a response based on the uploaded PDF file.

#### Session Validation

##### Empty Session

![Screenshot](screenshots/Empty%20Session%20Input.png)

- Send the chat while the Session Name is empty.

![Screenshot](screenshots/Empty%20Session%20Validation.png)

- It will get the validation that says **"Session name must not be empty."**

##### Duplicate Session

![Screenshot](screenshots/Session%20List.png)

- Click New chat button to add a new session.

![Screenshot](screenshots/Duplicate%20Session%20Text%20Input.png)

- Input the session that already exists in the list of sessions.

![Screenshot](screenshots/Duplicate%20Session%20Validation.png)

- It will get the validation that says :
  - **"Session name already exists. Please choose a different name."**

#### Delete All Sessions

![Screenshot](screenshots/Delete%20All%20Session%20Prompt.png)

- Click the button **"Delete all sessions"**

![Screenshot](screenshots/Delete%20All%20Sessions%20Confirmation.png)

- Click the button **"Yes, delete all sessions"** to proceed with deletion

![Screenshot](screenshots/Delete%20All%20Sessions%20Result.png)

- We have reset the sessions state and back to the initial state of the
  application where we don't have saved sessions.
