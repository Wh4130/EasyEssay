import streamlit as st
import pandas as pd
import time

from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager
from utils.sheet_manager import SheetManager
from utils.user_manager import UserManager
from utils.docs_manager import PineconeManager
from utils.others import Others


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
        st.caption(f"**Literature Review Tool**")

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
}</style>
""")

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** main function
def main():

    with st.sidebar:
        st.caption(f"Logged in as: **{st.session_state['user_id']}**")


    st.title("User Info")

    st.dataframe(
        pd.DataFrame(
            {"Nickname": [st.session_state['user_name']],
             "User ID": [st.session_state['user_id']],
             "Gmail": [st.session_state['user_email']],
             "Time for registration": [st.session_state['_registerTime']]}
        ),
        hide_index = True,
        width = 1000
    )

    # * 登出按鈕
    if st.button("Log Out", "logout", icon = ":material/logout:"):
        st.session_state['logged_in'] = False
        st.success("Logged Out")
        for session in ["user_email", "user_id", "_registerTime", "messages"]:
            del st.session_state[session]
        time.sleep(2)
        st.rerun()

    # * 刪除帳號按鈕
    if st.button("**:red[Delete the Account]**", "deregister", icon = ":material/report:"):
        UserManager.deregister()



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