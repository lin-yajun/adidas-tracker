import streamlit as st
import pandas as pd
import gspread
import json
import urllib.parse

st.set_page_config(page_title="全球 adidas 門市與概念店儀表板", layout="wide")

st.title("全球 adidas 門市與概念店儀表板")

@st.cache_data(ttl=60)
def load_data():
    try:
        creds_json = st.secrets["GOOGLE_CREDS"]
        if isinstance(creds_json, str):
            creds_dict = json.loads(creds_json)
        else:
            creds_dict = dict(creds_json)
            
        gc = gspread.service_account_from_dict(creds_dict)
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.sheet1
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"讀取資料失敗：{e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # 動態產生乾淨的 Google 地圖與網頁搜尋 URL (避免相對路徑跳轉問題)
    if "store_name" in df.columns:
        df["map_url"] = df.apply(
            lambda r: f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(str(r.get('store_name','')) + ' ' + str(r.get('address','')))}",
            axis=1
        )
        df["search_url"] = df["store_name"].apply(
            lambda name: f"https://www.google.com/search?q={urllib.parse.quote(str(name))}"
        )

    # 側邊欄篩選器
    st.sidebar.header("門市篩選器")
    countries = ["全部"] + list(df["country"].unique()) if "country" in df.columns else ["全部"]
    selected_country = st.sidebar.selectbox("選擇國家", countries)
    
    concepts = ["全部"] + list(df["concept"].unique()) if "concept" in df.columns else ["全部"]
    selected_concept = st.sidebar.selectbox("選擇門市類型", concepts)
    
    filtered_df = df.copy()
    if selected_country != "全部":
        filtered_df = filtered_df[filtered_df["country"] == selected_country]
    if selected_concept != "全部":
        filtered_df = filtered_df[filtered_df["concept"] == selected_concept]
        
    st.markdown(f"目前顯示 **{len(filtered_df)}** 筆門市資料")

    # 地圖展示
    if "lat" in filtered_df.columns and "lng" in filtered_df.columns:
        map_df = filtered_df.copy()
        map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
        map_df["lng"] = pd.to_numeric(map_df["lng"], errors="coerce")
        map_df = map_df.dropna(subset=["lat", "lng"])
        if not map_df.empty:
            st.subheader("📍 門市地圖分佈")
            st.map(map_df, latitude="lat", longitude="lng")

    # 表格展示 (設定正確的外連 LinkColumn)
    st.subheader("📋 門市詳細清單")
    
    display_cols = [c for c in ["store_id", "store_name", "photo", "map_url", "search_url", "country", "city", "address", "concept"] if c in filtered_df.columns]
    
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "photo": st.column_config.ImageColumn("門市照片"),
            "map_url": st.column_config.LinkColumn("📍 地圖導航", display_text="開啟地圖"),
            "search_url": st.column_config.LinkColumn("🔍 網頁搜尋", display_text="搜尋網頁")
        },
        use_container_width=True,
        hide_index=True
    )
