import streamlit as st
import pandas as pd
import gspread
import json

st.set_page_config(page_title="全球 adidas 店點追蹤", layout="wide")
st.title("全球 adidas 門市與概念店儀表板")

# 1. 連線至 Google Sheets
@st.cache_data(ttl=3600)
def load_data():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key(st.secrets["SPREADSHEET_ID"])
    data = sh.sheet1.get_all_records()
    return pd.DataFrame(data)

try:
    df = load_data()

    # 2. 側邊欄過濾器
    st.sidebar.header("門市篩選器")
    countries = st.sidebar.multiselect("選擇國家", options=df["country"].unique(), default=df["country"].unique())
    concepts = st.sidebar.multiselect("選擇門市系列", options=df["concept"].unique(), default=df["concept"].unique())

    filtered_df = df[(df["country"].isin(countries)) & (df["concept"].isin(concepts))]

    # 3. 數據統計與地圖
    st.metric("符合條件的門市數量", len(filtered_df))

    st.subheader("📍 全球地圖分布")
    if not filtered_df.empty:
        # 強制轉為浮點數以防型態錯誤
        filtered_df["lat"] = pd.to_numeric(filtered_df["lat"])
        filtered_df["lng"] = pd.to_numeric(filtered_df["lng"])
        st.map(filtered_df, latitude="lat", longitude="lng")

    # 4. 資料表格
    st.subheader("門市列表明細")
    st.dataframe(filtered_df[["store_name", "country", "city", "concept", "address", "updated_at"]], use_container_width=True)

except Exception as e:
    st.error(f"讀取資料失敗，請檢查 Secrets 設定：{e}")
