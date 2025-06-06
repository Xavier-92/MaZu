import streamlit as st
import pandas as pd
import os
from streamlit_calendar import calendar

def Home_page():
    st.header("📅 行事曆")
    # 讀取 Excel 活動
    CALENDAR_FILE = "calendar_events.xlsx"
    # 自動檢查並初始化 calendar_events.xlsx
    def init_calendar_file():
        df = pd.DataFrame(columns=["title", "start", "end"])
        df.to_excel(CALENDAR_FILE, index=False)
        return df
    if os.path.exists(CALENDAR_FILE):
        try:
            cal_df = pd.read_excel(CALENDAR_FILE)
            # 檢查欄位
            if not set(["title", "start", "end"]).issubset(set(cal_df.columns)):
                cal_df = init_calendar_file()
        except Exception as e:
            st.warning(f"calendar_events.xlsx 檔案損壞或格式錯誤，已自動重建。錯誤訊息: {e}")
            cal_df = init_calendar_file()
    else:
        cal_df = init_calendar_file()
    # 轉換成 events 格式
    events = []
    for _, row in cal_df.iterrows():
        event = {"title": row["title"], "start": str(row["start"])}
        if "end" in cal_df.columns and not pd.isna(row["end"]):
            event["end"] = str(row["end"])
        events.append(event)
    calendar(events=events, options={"initialView": "dayGridMonth"})
    st.markdown("---")
    return
