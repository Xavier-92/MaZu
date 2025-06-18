# pip install streamlit-calendar
# pip install openpyxl
# streamlit run streamlit_app.py
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
# from streamlit_folium import st_folium
from Google_API import get_coordinates
from home import Home_page
from pages import pages
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter
import time
import os
import folium


# =========================
# 管理員帳號密碼（僅管理員寫死於程式）
# =========================
USERS = {
    "admin": {"password": "1234", "role": "admin"},
    "punch": {"password": "1234", "role": "punch"}
}

# Excel 檔案名稱
EXCEL_FILE = "分靈資訊.xlsx"
# 一般帳號檔案
ACCOUNTS_FILE = "accounts.xlsx"
# 申請帳號暫存檔案
APPLY_FILE = "account_apply.xlsx"
# 初始化登入狀態與角色
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# =========================
# 登入區塊
# =========================

if not st.session_state.logged_in:
    st.title("🛕 分靈資訊管理系統 下方登入")
    Home_page ()
    st.markdown("---")
    st.subheader("登入系統")
    st.markdown("請輸入您的帳號與密碼進行登入。若尚未申請帳號，請點選下方的「申請帳號」按鈕。")
    username = st.text_input("帳號")
    password = st.text_input("密碼", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("登入"):
            # 管理員帳號驗證
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.role = USERS[username]["role"]
                st.success("登入成功！")
                st.rerun()
            else:
                # 一般帳號從 accounts.xlsx 讀取
                if os.path.exists(ACCOUNTS_FILE):
                    acc_df = pd.read_excel(ACCOUNTS_FILE, dtype={"帳號": str})
                    user_row = acc_df[(acc_df["帳號"] == str(username)) & (acc_df["密碼"] == password)]
                    if not user_row.empty:
                        st.session_state.logged_in = True
                        st.session_state.role = user_row.iloc[0]["角色"]
                        # 儲存帳號名稱於 session 供後續比對
                        st.session_state.username = username
                        st.success("登入成功！")
                        st.rerun()
                    else:
                        st.error("帳號或密碼錯誤，或尚未審核通過")
                else:
                    st.error("帳號或密碼錯誤，或尚未審核通過")
    with col2:
        if st.button("申請帳號"):
            st.session_state.show_apply = True
    # 帳號申請表單
    if st.session_state.get("show_apply", False):
        st.subheader("申請新帳號")
        apply_user = st.text_input("申請帳號名稱", key="apply_user")
        apply_pw = st.text_input("設定密碼", type="password", key="apply_pw")
        apply_contact = st.text_input("聯絡人姓名", key="apply_contact")
        apply_phone = st.text_input("聯絡電話", key="apply_phone")
        if st.button("送出申請"):
            if apply_user and apply_pw and apply_contact:
                if os.path.exists(APPLY_FILE):
                    apply_df = pd.read_excel(APPLY_FILE, dtype={"帳號": str})
                else:
                    apply_df = pd.DataFrame(columns=["帳號", "密碼", "聯絡人", "電話", "狀態"])
                # 檢查是否重複申請
                if (apply_df["帳號"] == apply_user).any():
                    st.warning("此帳號已申請，請等待審核或更換帳號名稱！")
                else:
                    apply_df = pd.concat([
                        apply_df,
                        pd.DataFrame([[str(apply_user), apply_pw, apply_contact, apply_phone, "待審核"]], columns=apply_df.columns)
                    ], ignore_index=True)
                    apply_df["帳號"] = apply_df["帳號"].astype(str)
                    apply_df.to_excel(APPLY_FILE, index=False)
                    st.success("申請已送出，請等待管理員審核！")
                    st.session_state.show_apply = False
            else:
                st.warning("請填寫完整資訊！")
    
    st.stop()

pages()