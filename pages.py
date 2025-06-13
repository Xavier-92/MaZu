import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
# from streamlit_folium import st_folium
from Google_API import get_coordinates
from home import Home_page
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter
import time
import os
import folium



def pages():
    # Excel 檔案名稱
    EXCEL_FILE = "分靈資訊.xlsx"
    # 一般帳號檔案
    ACCOUNTS_FILE = "accounts.xlsx"
    # 申請帳號暫存檔案
    APPLY_FILE = "account_apply.xlsx"

    # =========================
    # 分頁選單
    # =========================
    st.set_page_config(page_title="分靈資訊管理系統", layout="centered")
    st.sidebar.title("功能選單")
    # 管理員與一般使用者分開顯示功能
    if st.session_state.role == "admin":
        page_list = ["主頁&行事曆", "新增活動", "分靈地圖", "打卡紀錄", "新增分靈資訊", "現有分靈資訊", "帳號申請審核", "管理員信箱"]
    elif st.session_state.role == "punch":
        page_list = ["主頁&行事曆", "分靈地圖", "打卡", "管理員信箱"]
    else:
        page_list = ["主頁&行事曆", "分靈地圖", "新增分靈資訊", "管理員信箱"]
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

    elif page == "管理員信箱":
        st.title("📬 管理員信箱:有甚麼活動想要通知廟方?")
        MAILBOX_FILE = "admin_mailbox.xlsx"
        with st.form("mailbox_form", clear_on_submit=True):
            event_date = st.date_input("希望舉辦日期")
            event_content = st.text_area("想辦的活動內容", height=80)
            contact = st.text_input("最想要的聯絡方式（電話/Email/Line等）")
            submitted = st.form_submit_button("送出")
            if submitted:
                if event_content and contact:
                    import datetime
                    username = st.session_state.get("username", "")
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if os.path.exists(MAILBOX_FILE):
                        mailbox_df = pd.read_excel(MAILBOX_FILE)
                    else:
                        mailbox_df = pd.DataFrame(columns=["帳號", "填寫時間", "希望舉辦日期", "活動內容", "聯絡方式"])
                    new_row = pd.DataFrame([[username, now, event_date, event_content, contact]], columns=mailbox_df.columns)
                    mailbox_df = pd.concat([mailbox_df, new_row], ignore_index=True)
                    mailbox_df.to_excel(MAILBOX_FILE, index=False)
                    st.success("已送出，廟方將盡快與您聯絡！")
                else:
                    st.warning("請填寫活動內容與聯絡方式！")
        # 管理員可檢視與刪除留言
        if st.session_state.role == "admin":
            st.markdown("---")
            st.subheader("所有留言紀錄")
            if os.path.exists(MAILBOX_FILE):
                mailbox_df = pd.read_excel(MAILBOX_FILE)
                st.dataframe(mailbox_df, use_container_width=True)
                if len(mailbox_df) > 0:
                    del_idx = st.number_input("輸入要刪除的留言列編號（從 0 開始）", min_value=0, max_value=len(mailbox_df)-1, step=1, key="del_mailbox_idx")
                    if st.button("刪除留言"):
                        mailbox_df = mailbox_df.drop(index=del_idx).reset_index(drop=True)
                        mailbox_df.to_excel(MAILBOX_FILE, index=False)
                        st.success(f"已刪除第 {del_idx} 列留言")
                        st.rerun()
            else:
                st.info("目前沒有留言紀錄。")

    elif page == "分靈地圖":
        st.title("📍 分靈地址地圖標記")
        # 讀取分靈資訊（直接用全域 EXCEL_FILE，不要重複定義）
        df = pd.read_excel(EXCEL_FILE) if os.path.exists(EXCEL_FILE) else pd.DataFrame(columns=["帳號", "宮廟名稱", "聯絡人", "聯絡電話", "地址", "備註", "緯度", "經度"])
        # 過濾有經緯度的資料
        df = df.dropna(subset=["緯度", "經度"])
        if not df.empty:
            # 取第一筆作為地圖中心
            center_lat = df.iloc[0]["緯度"]
            center_lon = df.iloc[0]["經度"]
            m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
            for idx, row in df.iterrows():
                popup_text = f"<b>{row['宮廟名稱']}</b><br>地址: {row['地址']}"
                folium.Marker(
                    location=[row["緯度"], row["經度"]],
                    popup=popup_text,
                    tooltip=row["宮廟名稱"]
                ).add_to(m)
            from streamlit.components.v1 import html
            map_html = m._repr_html_()
            html(map_html, height=500)
        else:
            st.info("目前沒有可顯示的分靈地點（缺少經緯度資料）。")


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
                        info_df["會員卡號"] = info_df["會員卡號"].astype(str)
                        user_row = info_df[info_df["會員卡號"] == str(rfid)]
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
        if st.session_state.role == "admin":
            col1, col2 = st.columns(2)
            with col1:
                account_input = st.text_input("帳號")
                name = st.text_input("宮廟名稱")
                contact = st.text_input("聯絡人")
            with col2:
                phone = st.text_input("聯絡電話")
                address = st.text_input("地址")
                password_input = st.text_input("密碼", type="password")
            note = st.text_area("備註", height=100)
        else:
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
                if account_input and name and contact and password_input:
                    lat, lon = get_coordinates(address)
                    new_data = pd.DataFrame(
                        [[account_input, name, contact, phone, address, note, lat, lon]],
                        columns=["帳號", "宮廟名稱", "聯絡人", "聯絡電話", "地址", "備註", "緯度", "經度"]
                    )
                    df = pd.concat([df, new_data], ignore_index=True)
                    df.to_excel(EXCEL_FILE, index=False)
                    # 新增帳號到 accounts.xlsx
                    ACCOUNTS_FILE = "accounts.xlsx"
                    if os.path.exists(ACCOUNTS_FILE):
                        acc_df = pd.read_excel(ACCOUNTS_FILE)
                    else:
                        acc_df = pd.DataFrame(columns=["帳號", "密碼", "角色"])
                    if not (acc_df["帳號"] == account_input).any():
                        new_acc = pd.DataFrame([[account_input, password_input, "user"]], columns=["帳號", "密碼", "角色"])
                        acc_df = pd.concat([acc_df, new_acc], ignore_index=True)
                        acc_df.to_excel(ACCOUNTS_FILE, index=False)
                    st.success("✅ 分靈資訊與帳號已儲存！")
                    st.rerun()
                else:
                    st.warning("⚠️ 帳號、密碼、宮廟名稱與聯絡人為必填欄位！")
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
