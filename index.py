from utils.data_manager import DataManager
from utils.llm_manager import Summarizor
from utils.prompt_manager import PromptManager
from utils.sheet_manager import SheetManager
from utils.user_manager import UserManager
from utils.docs_manager import PineconeManager
from utils.others import Others

import streamlit as st
import datetime as dt
import random
import pandas as pd
import json
import requests
import time

st.set_page_config(page_title = "Easy Essay - Literature Summary Database", 
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

if "pinecone" not in st.session_state:
    st.session_state["pinecone"] = PineconeManager()

if "pinecone_idx_name" not in st.session_state:
    st.session_state["pinecone_idx_name"] = "easyessay"

if "messages" not in st.session_state:
    st.session_state["messages"] = {
        row["_fileId"]: {
            "doc_id": row["_fileId"],
            "doc_name": row["_fileName"],
            "doc_summary": row["_summary"],
            "chat_history": []
        }
        for _, row in st.session_state['user_docs'].iterrows()
    }

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
# *** Main
def main():
    st.title("Generate Literature Summary")
    
    # * 登入後顯示使用者名稱與重新整理按鈕
    with st.sidebar:
        if st.button("Refresh", "reload", icon = ":material/refresh:"):
            del st.session_state["pdfs_raw"]
            st.rerun()
            
        st.caption(f"Logged in as: **{st.session_state['user_id']}**")
        # Others.fetch_IP()
    
    # * 定義主要頁面分頁：摘要產生器 / 提示模板

    TAB_SUMMARIZE, TAB_PROMPT_TEMP = st.tabs(["Summary Generator", "Prompt Templates"])

    # *** 摘要產生器 ***
    with TAB_SUMMARIZE:
        # * 定義頁面區塊
        cl, cr = st.columns(2)
        with cl:
            button_upload = st.button("Upload", key = "upload", icon = ":material/upload:")
        with cr:
            button_start = st.button("Summarize", key = "summarize", type = "primary", icon = ":material/start:")
        
        if button_upload:
            DataManager.FORM_pdf_input()

        # * 定義資料預覽 CONTAINER
        BOX_PREVIEW = st.empty()

        # * 定義執行條件
        if button_start:
            # * First check if the raw data is prepared
            if st.session_state['pdfs_raw'].empty:
                st.warning("Please upload your document first！")
                st.stop()

            # * Check the sheet link
            client = SheetManager.authenticate_google_sheets()
            sheet_id = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user'])
            if sheet_id == None:
                st.stop()
            
        

            # TODO 這段，未來會想要前後端分開寫，並用 async
            BOX_PREVIEW.empty()
            # ** Generate Summary
            with st.spinner("Uploading documents..."):
                to_update = pd.DataFrame(columns = ["_fileId", "_fileName", "_summary", "_generatedTime", "_length", "_userId", "_tag"])
                progress_bar = st.progress(0, "(0%)Processing...")

                for i, row in st.session_state['pdfs_raw'].iterrows():
                    # generating unique index
                    while True:
                        fileID = DataManager.generate_random_index() 
                        if fileID not in st.session_state["user_docs"]["_fileId"].tolist():
                            break

                    # create data instance by schema 
                    doc_data_json = {
                        "fileid": fileID,
                        "filename": row['filename'].replace(" ", "_"),
                        "content": "\n".join(row['content']),
                        "user_id": st.session_state['user_id'],
                        "tag": row['tag'],
                        "lang": row['language'],
                        "additional_prompt": row['additional_prompt']
                    }

                    progress_bar.progress(i / len(st.session_state['pdfs_raw']), f"({round(i / len(st.session_state['pdfs_raw']), 2) * 100}%)「{row['filename'].replace(" ", "_")}」...")

                    # with st.spinner("Generating Summary..."):
                    #     prompt = PromptManager.summarize(row["language"], row["additional_prompt"])
                    #     model = Summarizor(language = row['language'], other_instruction = row["additional_prompt"])
                    #     response = model.apiCall(contents)
                    #     summary = Summarizor.find_json_object(response)

                    # * --- Send request to generate summary in background
                    response = requests.post("https://easyessaybackend.onrender.com/summarize", json = doc_data_json)
                    
                    # * --- Update the generated summary to cache
                    # to_update.loc[len(to_update), ["_fileId", "_fileName", "_summary", "_generatedTime", "_length", "_userId", "_tag"]] = [fileID, doc_data_json["filename"], "PENDING", dt.datetime.now().strftime("%I:%M%p on %B %d, %Y"), "", st.session_state['user_id'], st.session_state["tag"]]


                    # * --- Update the document to Pinecone Embedding Database
                    with st.spinner("Upserting pdfs to Pinecone Embedding Database..."):
                        st.session_state['pinecone'].insert_docs(
                            texts = row['content'],
                            namespace = fileID,
                            index_name = st.session_state['pinecone_idx_name']
                        )
                        # initialize chat history container
                        st.session_state['messages'][fileID] =  {
                            "doc_id": fileID,
                            "doc_name": doc_data_json["filename"],
                            "doc_summary": "",
                            "chat_history": []
                        }
                    
                    


                progress_bar.empty()

            # # ** Update to database
            # with st.spinner("Updating to database..."):
            #     # * acquire a lock  
            #     SheetManager.acquire_lock(st.session_state["sheet_id"], "user_docs")
            #     # * update
            #     for _, row in to_update.iterrows():
            #         SheetManager.insert(sheet_id, "user_docs", row.tolist())
            #     # * release the lock
            #     SheetManager.release_lock(st.session_state["sheet_id"], "user_docs")
            
            # ** Complete message
            st.success("All uploaded documents are being summarized in background. Please go to 『Literature Summary Database』 page to check the status later.")
            time.sleep(1.5)
            del st.session_state["user_docs"]
            del to_update
            st.rerun()

    # *** 提示模板 ***
    with TAB_PROMPT_TEMP:
        p = st.selectbox("Choose the prompt type", PromptManager.others().keys(), help = "可以將想要使用的提示模板複製貼上至『摘要產生器』頁面中的:blue[『額外提示 prompt』]欄位。")
        st.code(PromptManager.others()[p], language = None, wrap_lines = True)
            
    # *** 文獻原始資料預覽 ***
    with BOX_PREVIEW.container():
        preview_cache = st.data_editor(st.session_state["pdfs_raw"], 
                    disabled = ["length"], 
                    column_order = ["selected", "filename", "content", "tag", "language", "additional_prompt"],
                    column_config = {
                        "filename": st.column_config.TextColumn(
                            "Filename",
                            width = "medium",
                            max_chars = 200,
                            validate = r".+\.pdf"
                        ),
                        "content": None,
                        "tag": st.column_config.SelectboxColumn(
                            "Tag", 
                            help = "Tag for the literature",
                            width = "small",
                            options = st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["_tag"].tolist(),
                            required = True
                        ),
                        "language": st.column_config.SelectboxColumn(
                            "Language",
                            help = "Language that is used to generate the summary",
                            width = "small",
                            options = ["English", "Traditional Chinese", "Japanese"],
                            required = True
                        ),
                        "selected": st.column_config.CheckboxColumn(
                            "Select",
                            help = "Select the file that you want to summarize / delete"
                        ),
                        "additional_prompt": st.column_config.TextColumn(
                            "Additional Prompt",
                            help = "Additional instructions that you want to prompt the LLM (optional). \n You can type it on your own, or edit from existing prompt template.",
                            max_chars = 500
                        )
                    },
                    hide_index = True,
                    width = 1000)
        if st.button("Delete selected file", key = "delete_pdf", icon = ":material/delete:"):
            with st.spinner("Deleting"):
                st.session_state["pdfs_raw"] = preview_cache[preview_cache["selected"] == False]
                st.rerun()

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