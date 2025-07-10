
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st 
import pandas as pd
import time
import json

class SheetManager:

    @staticmethod
    def authenticate_google_sheets():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(st.secrets['gsheet-conn']['credits']), scope)
        client = gspread.authorize(creds)
        return client
    
    @staticmethod
    def extract_sheet_id(sheet_url):
        try:
            return sheet_url.split("/d/")[1].split("/")[0]
        except IndexError:
            st.error("無效的試算表連結，請檢查 URL 格式。")
            return None
        
    @staticmethod
    def fetch(sheet_id, worksheet):
        if sheet_id:
            client = SheetManager.authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                ws = sheet.worksheet(worksheet)
                data = ws.get_all_records()
                
                return pd.DataFrame(data)
            except:
                st.write("Connection Failed")

    @staticmethod
    def insert(sheet_id, worksheet, row: list):
        if sheet_id:
            client = SheetManager.authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.worksheet(worksheet)
                worksheet.freeze(rows = 1)
                worksheet.append_row(row)

                records = worksheet.get_all_records()
                
            except Exception as e:
                st.write(f"Connection Failed: {e}")

    @staticmethod
    def update(sheet_id, worksheet_name, row_idxs, column, values):
        mapping = {
            "user_docs": {
                "_fileId": "A",
                "_fileName": "B",
                "_summary": "C",
                "_generatedTime": "D",
                "_length": "E",
                "_userId": "F",
                "_tag": "G"
            },
            "user_tags": {
                "_tagId": "A",
                "_userId": "B",
                "_tag": "C"
            }
        }
        if sheet_id:
            client = SheetManager.authenticate_google_sheets()
            for idx, value in zip(row_idxs, values):
                try:
                    sheet = client.open_by_key(sheet_id)
                    worksheet = sheet.worksheet(worksheet_name)
                    pos = f"{mapping[worksheet_name][column]}{idx + 2}"
                    worksheet.update_acell(pos, value)
                    
                except Exception as e:
                    st.write(f"Connection Failed: {e}")

    @staticmethod
    def delete_row(sheet_id, worksheet_name, row_idxs: list):

        if not sheet_id:
            st.write("No sheet_id provided!")
            return
        
        while True:
            try:
                client = SheetManager.authenticate_google_sheets()

                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.worksheet(worksheet_name)

                if SheetManager.acquire_lock(sheet_id, worksheet_name):
                    for idx in sorted(row_idxs, reverse = True):
                        worksheet.delete_rows(idx + 2)
                    break
                else:
                    pass


            except Exception as e:
                st.write(f"Failed to delete row: {e}")
                break

    @staticmethod
    def acquire_lock(sheet_id, worksheet_name, timeout = 10):
        lock_maps = {
            "user_info": "F1",
            "user_docs": "H1",
            "user_tags": "D1"
        }

        """
        Acquire a lock before editing.
        :param worksheet: The gspread worksheet object.
        :param lock_pos: the position of the cell that stores the lock status
        :param timeout: Max time (in seconds) to wait for lock.
        :return: True if lock acquired, False otherwise.
        """
        start_time = time.time()
        client = SheetManager.authenticate_google_sheets()
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(worksheet_name)
        with st.spinner("Waiting for lock..."):
            while time.time() - start_time < timeout:
                lock_status = worksheet.acell(lock_maps[worksheet_name]).value

                if lock_status == "Unlocked":
                    # Acquire the lock
                    worksheet.update_acell(lock_maps[worksheet_name], st.session_state["user_id"])
                    
                    return True
                
                elif lock_status == st.session_state["user_id"]:
                    # Already locked by the same user
                    return True
                
                time.sleep(0.5)

        return False
    
    @staticmethod
    def release_lock(sheet_id, worksheet_name):
        """
        Release the lock after editing.
        :param worksheet: The gspread worksheet object.
        :param user_email: The email of the user trying to release the lock.
        :return: True if lock released, False otherwise.
        """
        lock_maps = {
            "user_info": "F1",
            "user_docs": "H1",
            "user_tags": "D1"
        }

        client = SheetManager.authenticate_google_sheets()
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(worksheet_name)
        lock_status = worksheet.acell(lock_maps[worksheet_name]).value

        if lock_status == st.session_state["user_id"]:
            worksheet.update_acell(lock_maps[worksheet_name], "Unlocked")
            return True
        else:
            st.write("Lock is not held by you!")
            return False