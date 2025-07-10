import streamlit as st
import pandas as pd
import time
from utils.data_manager import DataManager
from utils.llm_manager import ChatBot
from utils.prompt_manager import PromptManager
from utils.sheet_manager import SheetManager
from utils.user_manager import UserManager
from utils.docs_manager import PineconeManager
from utils.others import Others

st.set_page_config(page_title = "Easy Essay 文獻摘要工具", 
                   page_icon = ":material/history_edu:", 
                   layout="centered", 
                   initial_sidebar_state = "auto", 
                   menu_items={
        'Get Help': None,
        'Report a bug': "mailto:huang0jin@gmail.com",
        'About': """- Model - **Gemini** 1.5 Flash
- Database Design - Google Sheets
- Developed by - **[Wally, Huang Lin Chun](https://antique-turn-ad4.notion.site/Wally-Huang-Lin-Chun-182965318fa7804c86bdde557fa376f4)**"""
    })

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Session State Config
if "pdfs_raw" not in st.session_state:
    st.session_state["pdfs_raw"] = pd.DataFrame(columns = ["filename", "content", "tag", "language", "selected", "additional_prompt"])

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_infos" not in st.session_state:
    st.session_state["user_infos"] = ""

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

if "sheet_id" not in st.session_state:
    st.session_state["sheet_id"] = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user'])

if "user_docs" not in st.session_state:
    st.session_state['user_docs'] = SheetManager.fetch(st.session_state["sheet_id"], "user_docs")

if "user_tags" not in st.session_state:
    st.session_state["user_tags"] = SheetManager.fetch(st.session_state["sheet_id"], "user_tags")

if "messages" not in st.session_state:
    st.session_state.messages = []

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Sidebar Config
with st.sidebar:
    
    # * Icon & Title
    text_box, icon_box = st.columns((0.7, 0.3))
    with icon_box:
        st.markdown(f'''
                        <img class="image" src="data:image/jpeg;base64,{DataManager.image_to_b64(f"./pics/icon.png")}" alt="III Icon" style="width:500px;">
                    ''', unsafe_allow_html = True)
    with text_box:
        st.write(" ")
        st.header("Easy Essay")
        st.caption(f"**Literature Summary Database**")

    # * Pages
    st.page_link("./pages/page_account.py", label = 'Account', icon = ":material/account_circle:")
    if st.session_state["logged_in"]:
        st.page_link("index.py", label = 'Literature Summary Generator', icon = ":material/edit_square:")
        st.page_link("./pages/page_docs.py", label = 'Literature Summary Database', icon = ":material/folder_open:")
        st.page_link("./pages/page_chat.py", label = 'Chat with Literature', icon = ":material/mark_chat_unread:")


    Others.fetch_IP()  

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** HTML & CSS
st.html("""<style>
div.stButton > button {
    width: 100%;  /* 設置按鈕寬度為頁面寬度的 60% */
    height: 50px;
    margin-left: 0;
    margin-right: auto;
}
</style>
""")

def main():
    st.title("Chat with Literature")
    st.button("hehe")
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            

    chatBot = ChatBot()

    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            stream = chatBot.apiCall(prompt)
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})



# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Authentication
if st.session_state['logged_in'] == False:
    # * 登入頁面
    st.info("Welcome! Please login or sign up to use the tool.")
    entry_l, entry_r = st.columns(2)
    with entry_l:
        if st.button("Login", "login"):
            UserManager.log_in()
    with entry_r:
        if st.button("Sign Up", "register"):
            UserManager.register()

else:
    main()