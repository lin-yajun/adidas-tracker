import streamlit as st
import pandas as pd
import gspread
import json
import urllib.parse
from streamlit_folium import st_folium
import folium
import plotly.express as px

# 1. 頁面配置與自訂 CSS 主題
st.set_page_config(
    page_title="adidas Global Store Explorer",
    page_icon="👟",
    layout="wide"
)
# 🔐 密碼驗證邏輯
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.subheader("🔒 私人儀表板 - 請輸入存取密碼")
    password_input = st.text_input("密碼", type="password")
    
    if st.button("登入"):
        correct_password = st.secrets.get("APP_PASSWORD", "123456")
        if password_input == correct_password:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤，請重新輸入！")
            
    return False

if not check_password():
    st.stop()
# 套用 adidas 時尚黑白風格自訂 CSS
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stApp header { background-color: transparent; }
    h1 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; color: #111111; letter-spacing: -1px; }
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 5px solid #000000;
        text-align: center;
    }
    .store-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid #eeeeee;
    }
    .badge {
        background-color: #000000;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .btn-map {
        display: inline-block;
        background-color: #000000;
        color: #ffffff !important;
        padding: 6px 14px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 13px;
        font-weight: bold;
        margin-top: 8px;
    }
    .btn-map:hover { background-color: #333333; }
</style>
""", unsafe_allow_html=True)

st.title("👟 adidas Global Store Explorer")
st.caption("全球 adidas 直營店、品牌旗艦店與 Outlet 旗艦導航儀表板")

# 2. 讀取 Google 試算表資料
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
        st.error(f"⚠️ 讀取資料失敗，請檢查 Secrets 設定：{e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # 資料前處理解析 URL
    if "store_name" in df.columns:
        df["map_url"] = df.apply(
            lambda r: f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(str(r.get('store_name','')) + ' ' + str(r.get('address','')))}",
            axis=1
        )
        df["search_url"] = df["store_name"].apply(
            lambda name: f"https://www.google.com/search?q={urllib.parse.quote(str(name))}"
        )

    # 側邊欄篩選器
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/2/20/Adidas_Logo.svg", width=120)
    st.sidebar.title("門市篩選條件")
    
    countries = ["全部"] + sorted(list(df["country"].unique())) if "country" in df.columns else ["全部"]
    selected_country = st.sidebar.selectbox("🌏 選擇國家 / 地區", countries)
    
    concepts = ["全部"] + sorted(list(df["concept"].unique())) if "concept" in df.columns else ["全部"]
    selected_concept = st.sidebar.selectbox("🏬 選擇門市類型", concepts)
    
    # 關鍵字搜尋
    search_keyword = st.sidebar.text_input("🔍 搜尋門市名稱或地址", "")

    # 執行過濾
    filtered_df = df.copy()
    if selected_country != "全部":
        filtered_df = filtered_df[filtered_df["country"] == selected_country]
    if selected_concept != "全部":
        filtered_df = filtered_df[filtered_df["concept"] == selected_concept]
    if search_keyword:
        filtered_df = filtered_df[
            filtered_df["store_name"].astype(str).str.contains(search_keyword, case=False) |
            filtered_df["address"].astype(str).str.contains(search_keyword, case=False)
        ]

    # 3. 頂部關鍵指標列 (Metrics Dashboard)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("📍 顯示門市數量", f"{len(filtered_df)} 筆")
    with m2:
        st.metric("🌍 涵蓋國家", f"{filtered_df['country'].nunique() if 'country' in filtered_df else 0} 個")
    with m3:
        st.metric("🏙️ 涵蓋城市", f"{filtered_df['city'].nunique() if 'city' in filtered_df else 0} 個")
    with m4:
        st.metric("🏆 品牌旗艦/概念店", f"{len(filtered_df[filtered_df['concept'].str.contains('Center|Flagship', case=False, na=False)])} 間")

    st.markdown("---")

    # 分頁切換 (Tab Navigation)
    tab_map, tab_cards, tab_table, tab_charts = st.tabs(["🗺️ 互動地圖", "🎴 門市圖文卡片", "📋 詳細資料表格", "📊 統計數據分佈"])

    # --- TAB 1: 互動地圖 (Folium Map) ---
    with tab_map:
        st.subheader("📍 全球門市分佈地圖")
        map_df = filtered_df.copy()
        map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
        map_df["lng"] = pd.to_numeric(map_df["lng"], errors="coerce")
        map_df = map_df.dropna(subset=["lat", "lng"])

        if not map_df.empty:
            # 計算地圖中心點
            avg_lat = map_df["lat"].mean()
            avg_lng = map_df["lng"].mean()
            
            m = folium.Map(location=[avg_lat, avg_lng], zoom_start=5 if selected_country != "全部" else 2, tiles="CartoDB positron")

            for _, row in map_df.iterrows():
                # 依概念店類型區分顏色
                concept = str(row.get("concept", ""))
                color = "black"
                if "Brand Center" in concept or "Flagship" in concept:
                    color = "red"
                elif "Outlet" in concept:
                    color = "orange"
                elif "Originals" in concept:
                    color = "blue"

                popup_html = f"""
                <div style="font-family: Arial, sans-serif; width:220px;">
                    <h4 style="margin:0 0 5px 0;">{row['store_name']}</h4>
                    <span style="background-color:#000; color:#fff; padding:2px 6px; font-size:10px; border-radius:4px;">{row['concept']}</span>
                    <p style="font-size:12px; color:#555; margin:8px 0;">{row['address']}</p>
                    <a href="{row['map_url']}" target="_blank" style="display:inline-block; background:#000; color:#fff; padding:5px 10px; border-radius:4px; text-decoration:none; font-size:11px;">📍 開啟 Google 地圖導航</a>
                </div>
                """
                
                folium.Marker(
                    location=[row["lat"], row["lng"]],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=row["store_name"],
                    icon=folium.Icon(color=color, icon="shopping-bag", prefix="fa")
                ).add_to(m)

            st_folium(m, width="100%", height=500)
        else:
            st.warning("目前篩選條件下沒有包含經緯度的門市資料。")

    # --- TAB 2: 圖文卡片模式 (Card View) ---
    with tab_cards:
        st.subheader("🎴 門市圖文櫥窗")
        cols = st.columns(3)
        for idx, (_, row) in enumerate(filtered_df.iterrows()):
            col = cols[idx % 3]
            with col:
                img_url = row.get("image_url") if pd.notna(row.get("image_url")) and str(row.get("image_url")).startswith("http") else "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=500"
                
                st.markdown(f"""
                <div class="store-card">
                    <img src="{img_url}" style="width:100%; height:160px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                    <span class="badge">{row.get('concept', 'Store')}</span>
                    <h3 style="font-size:16px; margin:8px 0 4px 0;">{row.get('store_name')}</h3>
                    <p style="font-size:13px; color:#666; margin-bottom:8px;">📍 {row.get('address')}</p>
                    <a class="btn-map" href="{row.get('map_url')}" target="_blank">🗺️ 開啟導航</a>
                    <a class="btn-map" style="background-color:#555;" href="{row.get('search_url')}" target="_blank">🔍 搜尋網頁</a>
                </div>
                """, unsafe_allow_html=True)

    # --- TAB 3: 詳細表格模式 (Data Table) ---
    with tab_table:
        st.subheader("📋 門市完整數據庫")
        display_cols = [c for c in ["store_id", "store_name", "photo", "map_url", "search_url", "country", "city", "address", "concept"] if c in filtered_df.columns]
        
        st.dataframe(
            filtered_df[display_cols],
            column_config={
                "photo": st.column_config.ImageColumn("門市照片"),
                "map_url": st.column_config.LinkColumn("📍 地圖導航", display_text="開啟地圖"),
                "search_url": st.column_config.LinkColumn("🔍 網頁搜尋", display_text="搜尋門市")
            },
            use_container_width=True,
            hide_index=True
        )

    # --- TAB 4: 統計圖表 (Charts) ---
    with tab_charts:
        st.subheader("📊 門市分佈與類型分析")
        c1, c2 = st.columns(2)
        with c1:
            if "country" in filtered_df.columns:
                fig_country = px.pie(filtered_df, names="country", title="門市國家分佈比例", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set1)
                st.plotly_chart(fig_country, use_container_width=True)
        with c2:
            if "concept" in filtered_df.columns:
                fig_concept = px.bar(filtered_df["concept"].value_counts().reset_index(), x="concept", y="count", labels={"concept":"門市類型", "count":"數量"}, title="門市型態數量統計", color="concept")
                st.plotly_chart(fig_concept, use_container_width=True)
