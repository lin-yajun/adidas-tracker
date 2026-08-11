import streamlit as st
import pandas as pd
import gspread
import json

st.set_page_config(page_title="全球 adidas 門市與概念店儀表板", layout="wide")

st.title("全球 adidas 門市與概念店儀表板")

# 1. 讀取 Secrets 憑證
@st.cache_data(ttl=60) # 設定快取 60 秒過期，確保資料隨時同步最新 Google Sheets
def load_data():
    try:
        # 讀取 GOOGLE_CREDS
        creds_json = st.secrets["GOOGLE_CREDS"]
        if isinstance(creds_json, str):
            creds_dict = json.loads(creds_json)
        else:
            creds_dict = dict(creds_json)
            
        gc = gspread.service_account_from_dict(creds_dict)
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.sheet1
        
        # 讀取全部資料
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"讀取資料失敗，請檢查 Secrets 設定或欄位格式：{e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # 2. 左側邊欄篩選器
    st.sidebar.header("門市篩選器")
    
    # 國家篩選
    countries = ["全部"] + list(df["country"].unique()) if "country" in df.columns else ["全部"]
    selected_country = st.sidebar.selectbox("選擇國家", countries)
    
    # 概念店類型篩選
    concepts = ["全部"] + list(df["concept"].unique()) if "concept" in df.columns else ["全部"]
    selected_concept = st.sidebar.selectbox("選擇門市類型", concepts)
    
    # 過濾資料
    filtered_df = df.copy()
    if selected_country != "全部":
        filtered_df = filtered_df[filtered_df["country"] == selected_country]
    if selected_concept != "全部":
        filtered_df = filtered_df[filtered_df["concept"] == selected_concept]
        
    st.markdown(f"目前顯示 **{len(filtered_df)}** 筆門市資料")

    # 3. 地圖展示 (若有經緯度欄位才繪製)
    if "lat" in filtered_df.columns and "lng" in filtered_df.columns:
        # 確保經緯度轉為數字，並剔除無效值
        map_df = filtered_df.copy()
        map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
        map_df["lng"] = pd.to_numeric(map_df["lng"], errors="coerce")
        map_df = map_df.dropna(subset=["lat", "lng"])
        
        if not map_df.empty:
            st.subheader("📍 門市地圖分佈")
            st.map(map_df, latitude="lat", longitude="lng")

    # 4. 資料表格展示 (顯示相片與超連結)
    st.subheader("📋 門市詳細清單")
    
    # 格式化欄位展示
    display_cols = [c for c in ["store_id", "store_name", "photo", "map_link", "web_search", "country", "city", "address", "concept"] if c in filtered_df.columns]
    
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "photo": st.column_config.ImageColumn("門市照片"),
            "map_link": st.column_config.LinkColumn("地圖導航"),
            "web_search": st.column_config.LinkColumn("網頁搜尋")
        },
        use_container_width=True,
        hide_index=True
    )
