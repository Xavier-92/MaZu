# pip install streamlit-calendar
# pip install openpyxl
# streamlit run streamlit_app.py
import streamlit as st
from streamlit_calendar import calendar
# from streamlit_folium import st_folium
import pandas as pd
from Google_API import get_coordinates
from home import Home_page
import os
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter
import time


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
                    acc_df = pd.read_excel(ACCOUNTS_FILE)
                    user_row = acc_df[(acc_df["帳號"] == username) & (acc_df["密碼"] == password)]
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
                    apply_df = pd.read_excel(APPLY_FILE)
                else:
                    apply_df = pd.DataFrame(columns=["帳號", "密碼", "聯絡人", "電話", "狀態"])
                # 檢查是否重複申請
                if (apply_df["帳號"] == apply_user).any():
                    st.warning("此帳號已申請，請等待審核或更換帳號名稱！")
                else:
                    apply_df = pd.concat([
                        apply_df,
                        pd.DataFrame([[apply_user, apply_pw, apply_contact, apply_phone, "待審核"]], columns=apply_df.columns)
                    ], ignore_index=True)
                    apply_df.to_excel(APPLY_FILE, index=False)
                    st.success("申請已送出，請等待管理員審核！")
                    st.session_state.show_apply = False
            else:
                st.warning("請填寫完整資訊！")
    
    st.stop()

# =========================
# 分頁選單
# =========================
st.set_page_config(page_title="分靈資訊管理系統", layout="centered")
st.sidebar.title("功能選單")
# 管理員與一般使用者分開顯示功能
if st.session_state.role == "admin":
    page_list = ["主頁&行事曆", "新增活動", "打卡紀錄", "新增分靈資訊", "現有分靈資訊", "帳號申請審核"]
elif st.session_state.role == "punch":
    page_list = ["主頁&行事曆", "打卡"]
else:
    page_list = ["主頁&行事曆", "新增分靈資訊"]
page = st.sidebar.radio("請選擇功能頁面：", page_list)

st.title("🛕 分靈資訊管理系統")
st.markdown("---")

# =========================
# 主頁&行事曆
# =========================
if page == "主頁&行事曆":
    Home_page ()

 
elif page == "新增活動" and st.session_state.role == "admin":
    CALENDAR_FILE = "calendar_events.xlsx"
    if st.session_state.role == "admin":
        st.subheader("新增活動")
        new_title = st.text_input("活動名稱")
        new_start = st.date_input("開始日期")
        new_end = st.date_input("結束日期（可選）", value=new_start)
        if st.button("新增活動"):
            # 建立檔案或讀取
            if os.path.exists(CALENDAR_FILE):
                cal_df = pd.read_excel(CALENDAR_FILE)
            else:
                cal_df = pd.DataFrame(columns=["title", "start", "end"])
            # 新增資料
            cal_df = pd.concat([
                cal_df,
                pd.DataFrame([[new_title, new_start, new_end]], columns=["title", "start", "end"])
            ], ignore_index=True)
            cal_df.to_excel(CALENDAR_FILE, index=False)
            st.success("活動已新增！")
            st.rerun()

        # 活動管理（刪除/修改）
        st.subheader("活動管理")
        if os.path.exists(CALENDAR_FILE):
            cal_df = pd.read_excel(CALENDAR_FILE)
            if len(cal_df) > 0:
                st.dataframe(cal_df, use_container_width=True)
                # 刪除活動
                del_idx = st.number_input("輸入要刪除的活動列編號（從 0 開始）", min_value=0, max_value=len(cal_df)-1, step=1, key="del_event_idx")
                if st.button("刪除活動"):
                    cal_df = cal_df.drop(index=del_idx).reset_index(drop=True)
                    cal_df.to_excel(CALENDAR_FILE, index=False)
                    st.success(f"已刪除第 {del_idx} 列活動")
                    st.rerun()
                # 修改活動
                st.markdown("---")
                st.write("修改活動（請先輸入要修改的列編號）")
                edit_idx = st.number_input("輸入要修改的活動列編號（從 0 開始）", min_value=0, max_value=len(cal_df)-1, step=1, key="edit_event_idx")
                if len(cal_df) > 0:
                    edit_title = st.text_input("新活動名稱", value=str(cal_df.iloc[edit_idx]["title"]))
                    edit_start = st.date_input("新開始日期", value=pd.to_datetime(cal_df.iloc[edit_idx]["start"]))
                    edit_end = st.date_input("新結束日期", value=pd.to_datetime(cal_df.iloc[edit_idx]["end"]))
                    if st.button("儲存修改", key="save_event_edit"):
                        cal_df.at[edit_idx, "title"] = edit_title
                        cal_df.at[edit_idx, "start"] = edit_start
                        cal_df.at[edit_idx, "end"] = edit_end
                        cal_df.to_excel(CALENDAR_FILE, index=False)
                        st.success(f"已修改第 {edit_idx} 列活動")
                        st.rerun()
            else:
                st.info("目前沒有活動紀錄。")
        else:
            st.info("目前沒有活動紀錄。")


elif page == "分靈地圖" and st.session_state.role == "admin":
    st.title("📍 分靈地址地圖標記")
    # 載入 Excel
    EXCEL_FILE = "分靈資訊.xlsx"  # 請改為你自己的檔名
    # try:
    #     df = pd.read_excel(EXCEL_FILE)
    # except FileNotFoundError:
    #     st.error("找不到分靈資料檔案，請確認檔名與路徑。")
    #     st.stop()

    # # 檢查地址欄
    # if "地址" not in df.columns:
    #     st.error("Excel 裡找不到『地址』欄位！")
    #     st.stop()

    # # 初始化 geopy
    # geolocator = Nominatim(user_agent="map_demo")
    # geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)  # 限速避免被封鎖

    # # 新增經緯度欄位
    # latitudes = []
    # longitudes = []

    # st.info("🔄 轉換地址中，請稍候...")

    # for addr in df["地址"]:
    #     if pd.isna(addr):
    #         latitudes.append(None)
    #         longitudes.append(None)
    #         continue

    #     location = geocode(addr)
    #     if location:
    #         latitudes.append(location.latitude)
    #         longitudes.append(location.longitude)
    #     else:
    #         latitudes.append(None)
    #         longitudes.append(None)

    # df["lat"] = latitudes
    # df["lon"] = longitudes

    # # 過濾掉失敗的座標
    # map_df = df.dropna(subset=["lat", "lon"])

    # # 顯示地圖
    # if not map_df.empty:
    #     st.success(f"✅ 成功標記 {len(map_df)} 筆地址！")
    #     st.map(map_df[["lat", "lon"]])
    # else:
    #     st.warning("⚠️ 無任何可顯示的地點")



# =========================
# 管理員：打卡紀錄
# =========================
elif page == "打卡紀錄" and st.session_state.role == "admin":
    st.header("📋 打卡紀錄")
    punch_file = "punch_records.xlsx"
    if os.path.exists(punch_file):
        punch_df = pd.read_excel(punch_file)
        st.dataframe(punch_df, use_container_width=True)
    else:
        st.info("目前沒有打卡紀錄。")
    
# =========================
# 管理員：現有分靈資訊
# =========================
elif page == "現有分靈資訊" and st.session_state.role == "admin":
    st.subheader("🔍 查詢分靈資訊")
    search_term = st.text_input("請輸入關鍵字（宮廟名稱、聯絡人、地址）")

    df = pd.read_excel(EXCEL_FILE) if os.path.exists(EXCEL_FILE) else pd.DataFrame(columns=["帳號", "宮廟名稱", "聯絡人", "聯絡電話", "地址", "備註", "緯度", "經度"])
    if search_term:
        filtered_df = df[df.apply(lambda row: search_term.lower() in str(row["宮廟名稱"]).lower()
                                                 or search_term.lower() in str(row["聯絡人"]).lower()
                                                 or search_term.lower() in str(row["地址"]).lower(), axis=1)]
    else:
        filtered_df = df
    st.dataframe(filtered_df, use_container_width=True)

    st.header("📋 現有分靈資訊")
    st.dataframe(df, use_container_width=True)
    # 會員卡號編輯功能
    st.subheader("🗝️ 編輯會員卡號")
    if len(df) > 0:
        edit_idx = st.number_input("請輸入要編輯的資料列編號（從 0 開始）", min_value=0, max_value=len(df)-1, step=1, key="edit_card_idx")
        # 若尚未有會員卡號欄，則補上
        if "會員卡號" not in df.columns:
            df["會員卡號"] = ""
        current_card = str(df.iloc[edit_idx]["會員卡號"]) if "會員卡號" in df.columns else ""
        new_card = st.text_input("會員卡號", value=current_card, key=f"edit_card_{edit_idx}")
        if st.button("儲存會員卡號", key=f"save_card_{edit_idx}"):
            df.at[edit_idx, "會員卡號"] = new_card
            df.to_excel(EXCEL_FILE, index=False)
            st.success(f"已更新第 {edit_idx} 列會員卡號！")
            st.rerun()
    st.subheader("🗑️ 刪除資料")
    delete_index = st.number_input("請輸入要刪除的資料列編號（從 0 開始）", min_value=0, max_value=len(df)-1 if len(df) > 0 else 0, step=1, key="delete_idx")
    if st.button("刪除該列資料"):
        if len(df) > 0 and delete_index < len(df):
            df = df.drop(index=delete_index).reset_index(drop=True)
            df.to_excel(EXCEL_FILE, index=False)
            st.success(f"已刪除第 {delete_index} 列資料")
            st.rerun()
        else:
            st.warning("輸入的列編號無效")
    with open(EXCEL_FILE, "rb") as f:
        st.download_button("📥 下載 Excel 檔案", f, file_name=EXCEL_FILE)

# =========================
# 管理員：帳號申請審核與帳號狀態總覽
# =========================
elif page == "帳號申請審核" and st.session_state.role == "admin":
    st.header("帳號申請審核 & 帳號狀態總覽")
    # 顯示所有帳號申請狀態
    if os.path.exists(APPLY_FILE):
        apply_df = pd.read_excel(APPLY_FILE)
        if len(apply_df) > 0:
            st.subheader("所有帳號申請狀態")
            st.dataframe(apply_df, use_container_width=True)
            for idx, row in apply_df.iterrows():
                st.write(f"申請帳號：{row['帳號']}，聯絡人：{row['聯絡人']}，電話：{row['電話']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"核准_{idx}"):
                        if os.path.exists(ACCOUNTS_FILE):
                            acc_df = pd.read_excel(ACCOUNTS_FILE)
                        else:
                            acc_df = pd.DataFrame(columns=["帳號", "密碼", "角色"])
                        if not (acc_df["帳號"] == row['帳號']).any():
                            acc_df = pd.concat([
                                acc_df,
                                pd.DataFrame([[row['帳號'], str(row['密碼']), "user"]], columns=acc_df.columns)
                            ], ignore_index=True)
                            acc_df.to_excel(ACCOUNTS_FILE, index=False)
                        
                        # 核准後將申請人從申請列表刪除
                        apply_df = apply_df.drop(idx).reset_index(drop=True)
                        apply_df.to_excel(APPLY_FILE, index=False)
                        st.success(f"已核准 {row['帳號']}！")
                        st.rerun()
                with col2:
                    if st.button(f"刪除_{idx}"):
                        apply_df = apply_df.drop(idx).reset_index(drop=True)
                        apply_df.to_excel(APPLY_FILE, index=False)
                        st.warning(f"已刪除 {row['帳號']} 申請")
                        st.rerun()
        else:
            st.info("目前沒有待審核的帳號申請。")
    else:
        st.info("目前沒有帳號申請紀錄。")
    # 顯示所有已核准帳號
    st.subheader("所有已核准帳號")
    if os.path.exists(ACCOUNTS_FILE):
        acc_df = pd.read_excel(ACCOUNTS_FILE)
        st.dataframe(acc_df, use_container_width=True)
    else:
        st.info("目前沒有已核准帳號紀錄。")

# =========================
# 讀卡機介面：感應RFID TAG 按下輸入 則在 punch_records.xlsx 紀錄卡號、帳號、時間與日期
# =========================
elif page == "打卡" and st.session_state.role == "punch":
    st.header("🔄 會員打卡")
    st.write("請將 RFID Tag 靠近讀卡機，並按下「輸入」按鈕。")

    with st.form("punch_form", clear_on_submit=True):
        rfid = st.text_input("RFID Tag 編號", key="rfid_input")
        submitted = st.form_submit_button("輸入")

        if rfid:
            import datetime
            import pytz
            tz = pytz.timezone("Asia/Taipei")
            now = datetime.datetime.now(tz)
            punch_file = "punch_records.xlsx"
            info_file = "分靈資訊.xlsx"

            # 讀取分靈資訊，查找會員卡號對應帳號
            if os.path.exists(info_file):
                info_df = pd.read_excel(info_file)
                if "會員卡號" in info_df.columns:
                    user_row = info_df[info_df["會員卡號"].astype(str) == str(rfid)]
                    if not user_row.empty:
                        username = user_row.iloc[0]["帳號"]
                    else:
                        username = ""
                else:
                    username = ""
            else:
                username = ""

            if username:
                if os.path.exists(punch_file):
                    punch_df = pd.read_excel(punch_file)
                else:
                    punch_df = pd.DataFrame(columns=["帳號", "RFID Tag", "打卡時間"])
                punch_df = pd.concat([
                    punch_df,
                    pd.DataFrame([[username, rfid, now.strftime("%Y-%m-%d %H:%M:%S")]], columns=punch_df.columns)
                ], ignore_index=True)
                punch_df.to_excel(punch_file, index=False)
                st.success(f"✅ 打卡成功！帳號：{username}，RFID Tag：{rfid}，時間：{now.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.warning("⚠️ 查無此 RFID Tag 對應的帳號，請確認卡號是否正確！")
        else:
            st.warning("⚠️ 請先感應 RFID Tag！")
        
# =========================
# 管理員：新增分靈資訊
# 一般使用者：填寫分靈資訊（僅能填寫一則）: 未來改成google map API
# =========================
elif page == "新增分靈資訊" :

    EXCEL_FILE = "分靈資訊.xlsx"
    # Initialize session state for user login and role
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "role" not in st.session_state:
        st.session_state.role = None

    # Page for adding spiritual information
    st.header("➕ 新增分靈資訊")
    username = st.session_state.get("username", "")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("宮廟名稱")
        contact = st.text_input("聯絡人")
    with col2:
        phone = st.text_input("聯絡電話")
        address = st.text_input("地址")
    note = st.text_area("備註", height=100)

    # Read Excel file
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
    else:
        df = pd.DataFrame(columns=["帳號", "宮廟名稱", "聯絡人", "聯絡電話", "地址", "備註", "緯度", "經度"])

    # User role handling
    if st.session_state.role == "admin":
        if st.button("儲存"):
            if name and contact:
                lat, lon = get_coordinates(address)
                new_data = pd.DataFrame(
                    [[username, name, contact, phone, address, note, lat, lon]],
                    columns=["帳號", "宮廟名稱", "聯絡人", "聯絡電話", "地址", "備註", "緯度", "經度"]
                )
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_excel(EXCEL_FILE, index=False)
                st.success("✅ 資料已儲存！")
                st.rerun()
            else:
                st.warning("⚠️ 宮廟名稱與聯絡人為必填欄位！")
    else:
        already_exists = (df["帳號"] == username).any()
        if st.button("儲存"):
            if already_exists:
                st.warning("⚠️ 您已新增過資料，無法重複輸入。")
            elif name and contact:
                lat, lon = get_coordinates(address)
                new_data = pd.DataFrame([[username, name, contact, phone, address, note, lat, lon]], columns=["帳號", "宮廟名稱", "聯絡人", "聯絡電話", "地址", "備註", "緯度", "經度"])
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_excel(EXCEL_FILE, index=False)
                st.success("✅ 資料已儲存！")
            else:
                st.warning("⚠️ 宮廟名稱與聯絡人為必填欄位！")

# =========================
# 登出按鈕
# =========================
if st.button("登出"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()
