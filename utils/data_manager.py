import streamlit as st
from pypdf import PdfReader
import json
import base64
import string
import random

class DataManager:

    @staticmethod
    @st.dialog("請上傳欲處理的檔案（pdf）")
    def FORM_pdf_input():
        pdf_uploaded = st.file_uploader("**請上傳 pdf 檔案（支援多檔案上傳）**", accept_multiple_files = True)
        language = st.selectbox("請選擇摘要語言", ["Traditional Chinese", "English", "Japanese"])
        tag = st.selectbox("請選擇文件類別標籤", st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["_tag"].tolist())
        instructions = st.text_area("請輸入額外的摘要提示（Optional）")
        if st.button("確認"):
            if language is None:
                st.warning("請選擇語言")
                st.stop()
            if pdf_uploaded:
                for file in pdf_uploaded:
                    if file.name not in st.session_state["pdfs_raw"]["filename"]:
                        pdf_in_messages = DataManager.load_pdf(file)
                        st.session_state["pdfs_raw"].loc[len(st.session_state["pdfs_raw"]), ["filename", "content", "tag", "language", "selected", "additional_prompt"]] = [file.name, pdf_in_messages, tag, language, False, instructions]
                st.session_state["lang"] = language
                st.session_state["other_prompt"] = instructions if instructions else "None"
                st.session_state["tag"] = tag
            else:
                st.warning("請上傳檔案")
                st.stop()
            st.rerun()

    @staticmethod
    @st.cache_data
    def load_pdf(uploaded):

        '''load pdf data from user upload with caching'''
        reader = PdfReader(uploaded)
        number_of_pages = len(reader.pages)
        texts = []
        for i in range(number_of_pages):
            page = reader.pages[i]
            texts.append(f"【page {i}】\n" + page.extract_text())

        return "\n".join(texts)
    
    @staticmethod
    def find_json_object(input_string):
        '''catch the JSON format from LLM response'''

        # Match JSON-like patterns
        input_string = input_string.replace("\n", '').strip()
        input_string = input_string.encode("utf-8").decode("utf-8")
        start_index = input_string.find('{')
        end_index = input_string.rfind('}')

        if start_index != -1 and end_index != -1:
            json_string = input_string[start_index:end_index+1]
            try:
                json_object = json.loads(json_string)
                return json_object
            except json.JSONDecodeError:
                return "DecodeError"
        # st.write(json_string)

        return None  # Return None if no valid JSON is found
    
    # --- Transform Picture to Base64
    @staticmethod
    def image_to_b64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    
    # --- Generate a random index for document
    def generate_random_index():
        characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
        return ''.join(random.choices(characters, k = 8))