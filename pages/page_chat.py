import streamlit as st
import pandas as pd
import time
from datetime import datetime
import io
from utils.data_manager import DataManager
from utils.llm_manager import ChatBot
from utils.prompt_manager import PromptManager
from utils.sheet_manager import SheetManager
from utils.user_manager import UserManager
from utils.docs_manager import PineconeManager
from utils.others import Others
from utils.constants import Consts

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

if "ChatBot" not in st.session_state:
    st.session_state["ChatBot"] = ChatBot()

if "PineconeDB" not in st.session_state:
    st.session_state["PineconeDB"] = PineconeManager()

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

if "characters" not in st.session_state:
    st.session_state["characters"] = {
        "user": ":material/face_3:",
        "assistant": ":material/robot_2:",
        "system": ":material/brightness_alert:"
    }

if "chat_params" not in st.session_state:
    st.session_state["chat_params"] = {
        "RAG_strictness": "high",
        "doc_id": "N/A",
        "summary": "N/A",
        "top_k": 5,
        "additional_sys_prompt": None
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
}
</style>
""")

st.html("""<style>
div.stDownloadButton > button {
    width: 100%;  /* 設置按鈕寬度為頁面寬度的 60% */
    height: 50px;
    margin-left: 0;
    margin-right: auto;
}
</style>
""")

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Function that renders selectbox for tags and documents
def ConfigLiterature():
    selected_tag = st.selectbox(":material/bookmark: Select a tag", [key.replace(" ", "_") for key in st.session_state['user_tags'][st.session_state['user_tags']['_userId'] == st.session_state["user_id"]]['_tag']])
    XOR1 = st.session_state['user_docs']['_userId'] == st.session_state["user_id"]     # 篩出該 user 之文件
    XOR2 = st.session_state['user_docs']["_tag"] == selected_tag                       # 篩出該 user 之 tag
    selected_file = st.selectbox(":material/book_ribbon: Select a file to chat", [key.replace(" ", "_") for key in st.session_state['user_docs'][XOR1 & XOR2]['_fileName']])

    if selected_file:
        doc_id = st.session_state['user_docs'].loc[st.session_state['user_docs']['_fileName'] == selected_file, '_fileId'].tolist()[0]
        summary = st.session_state['user_docs'].loc[st.session_state['user_docs']['_fileName'] == selected_file, '_summary'].tolist()[0]

        st.session_state['chat_params']["doc_id"] = doc_id
        st.session_state['chat_params']["summary"] = summary
    else:
        st.session_state['chat_params']["doc_id"] = None
        st.session_state['chat_params']["summary"] = None
# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Function that allows modification for LLM setting
def ConfigLLM():
    # * Model selection
    selected_model = st.selectbox(":material/toggle_on: Select the model", Consts.gemini_model_list)
    st.session_state["ChatBot"].changeModel(selected_model)

    # * Set top_k
    top_k = st.slider(":material/linear_scale: Select parameter k", 
                      value = 5,
                      min_value = 1, 
                      max_value = 20, 
                      help = """When you ask question, before sending your question to the AI model, the backend program first :blue[queries the **k** most similar text chunks from the literature], and then provides the result texts to AI model so that it can answer more precisely. 
                      
The higher :blue[**k**] is, the more contextual information is provided to AI. """)
    
    st.session_state["chat_params"]['top_k'] = top_k

# * - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# *** Function for the UI of chat history saving, and chat system prompt addition.
def ConfigChat():

    @st.dialog("Add additional system instructions")
    def additional_chat_sys_prompt():
        additional_prompts = st.text_area(
            "Additional system instructions.",
            value = st.session_state["chat_params"]["additional_sys_prompt"])
        if st.button("Save"):
            st.session_state["chat_params"]["additional_sys_prompt"] = additional_prompts
            st.rerun()

    if st.button("Customize System Prompts"):
        additional_chat_sys_prompt()


    # * Chat History Download
    st.caption(f"**:gray[Download Chat History]**", help = """1. First, click the **:blue[Prepare Chat History]** button.
2. Then click the download button on the right hand side. The download will start automatically. 
               
Chat histories will be saved in excel format.
""")
    chat_l, chat_r = st.columns((0.8, 0.2))
    chat_hist_io = b""

    with chat_l:
        if st.button("Prepare Chat History", "transform_chat_history"):
            chat_hist_io = DataManager.compile_chat_histories(st.session_state["messages"])
    
    with chat_r:
        st.download_button(
            label    = "",
            data     = chat_hist_io,
            mime     = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_name = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            icon     = ":material/download:",
            type     = "primary" if chat_hist_io else "secondary"
        )

def main():

    with st.sidebar:
        # * Selection box for selecting documents to chat with
        with st.container(border = True, height = 310):
            st.subheader(":material/settings: Settings")

            TAB_DOCS, TAB_MODEL, TAB_CHAT = st.tabs(["Literature", "Model", "Chat"])

            with TAB_DOCS:
                ConfigLiterature()
            with TAB_MODEL:
                ConfigLLM()
            with TAB_CHAT:
                ConfigChat()

        

        
        st.caption(f"Logged in as: **{st.session_state['user_id']}**")

    st.title("Chat with Literature")
    if not st.session_state['chat_params']["doc_id"]:
            st.warning("There is no literature under the selected tag. Please upload the literature in **Literature Sumary Generator** under the tag or choose other tags.")
            st.stop()


    with st.container(border = True):
        st.markdown(st.session_state['chat_params']['summary'], unsafe_allow_html = True)

    
    

    if st.session_state.messages[st.session_state['chat_params']['doc_id']]['chat_history'] == []:
        with st.chat_message("assistant", avatar = st.session_state["characters"]["assistant"]):
            st.markdown("**:blue[Ask me something about the paper!]**")
    
    for i, message in enumerate(
        st.session_state.messages[st.session_state['chat_params']['doc_id']]['chat_history']
        ):
        with st.chat_message(message["role"], avatar = st.session_state["characters"][message["role"]]):
            st.markdown(message["content"])

        if (i != 0) & ( (i == 5) | (i % 15 == 0) ):
            with st.chat_message(message["role"], avatar = st.session_state["characters"]["system"]):
                st.info("**Warning: Chat history disappears automatically if you do not download it manually.**")
            
            


    if in_message := st.chat_input("Ask something regarding the selected literature:"):

        # *** --- User Input
        # Add user message to chat history
        (st.session_state.messages[st.session_state['chat_params']['doc_id']]['chat_history']
         .append({"role": "user", 
                  "content": in_message, 
                  "time": datetime.now(),
                  "model": st.session_state["ChatBot"].model_key}))
        # Display user message in chat message container
        with st.chat_message("user", avatar = st.session_state["characters"]["user"]):
            st.markdown(in_message)

        # *** --- Query from Pinecone Embedding DB
        similar_text_ls = st.session_state["PineconeDB"].search(
                                            query = in_message, 
                                            k = st.session_state["chat_params"]['top_k'], 
                                            namespace = st.session_state["chat_params"]["doc_id"],   # napespace = document ID
                                            index_name = "easyessay"
        )

        # Display assistant response in chat message container
        try:
            with st.chat_message("assistant", avatar = st.session_state["characters"]["assistant"]):
                
                stream = (st.session_state["ChatBot"]
                          .apiCall(in_message,
                                   similar_text_ls,
                                    doc_summary = st.session_state["chat_params"]["summary"],
                                    additional_prompt = st.session_state["chat_params"]["additional_sys_prompt"]))
                
                
                response = st.write_stream(stream)

                if not st.session_state["ChatBot"].checkRagAvailability(st.session_state["chat_params"]["doc_id"]):
                    st.warning("This literature is not in the vector database, so the answer is only based on the summary!")
                
                (st.session_state.messages[st.session_state['chat_params']['doc_id']]['chat_history']
                .append({"role": "assistant", 
                         "content": response, 
                         "time": datetime.now(),
                         "model": st.session_state["ChatBot"].model_key}))
            
        except Exception as e:
            st.write(e)
            with st.chat_message("assistant", avatar = st.session_state["characters"]["system"]):
                st.error("**We encountered some errors when connecting to Gemini API... Please try again later. Remember to save the chat history if needed!**")




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