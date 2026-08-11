import os
import json
import urllib.parse
import pandas as pd
import gspread

ALL_STORES = [
    # --- 台灣門市 ---
    {"store_id": "TW001", "store_name": "adidas Brand Center 台北品牌概念店", "country": "Taiwan", "city": "台北市", "address": "台北市信義區松壽路18號", "lat": 25.0355, "lng": 121.5672, "concept": "Brand Center", "image_url": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=500"},
    {"store_id": "TW002", "store_name": "adidas 忠孝門市", "country": "Taiwan", "city": "台北市", "address": "台北市大安區忠孝東路四段183號", "lat": 25.0416, "lng": 121.5518, "concept": "Performance Store", "image_url": "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=500"},
    {"store_id": "TW003", "store_name": "adidas Originals 南西門市", "country": "Taiwan", "city": "台北市", "address": "台北市中山區中山北路二段16巷3號", "lat": 25.0531, "lng": 121.5208, "concept": "Originals Store", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"},
    {"store_id": "TW004", "store_name": "adidas 西門町門市", "country": "Taiwan", "city": "台北市", "address": "台北市萬華區峨眉街21號", "lat": 25.0435, "lng": 121.5068, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW011", "store_name": "adidas 新竹巨城門市", "country": "Taiwan", "city": "新竹市", "address": "新竹市東區中央路229號1F", "lat": 24.8097, "lng": 120.9751, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW012", "store_name": "adidas 台中綠園道概念店", "country": "Taiwan", "city": "台中市", "address": "台中市西區公益路68號", "lat": 24.1511, "lng": 120.6638, "concept": "Brand Center", "image_url": ""},
    {"store_id": "TW018", "store_name": "adidas 高雄漢神巨蛋門市", "country": "Taiwan", "city": "高雄市", "address": "高雄市左營區博愛二路777號8F", "lat": 22.6695, "lng": 120.3023, "concept": "Performance Store", "image_url": ""},
    
    # --- 海外門市 ---
    {"store_id": "JP001", "store_name": "adidas Brand Center RAYARD MIYASHITA PARK", "country": "Japan", "city": "Tokyo", "address": "6-20-10 Jingumae, Shibuya-ku, Tokyo", "lat": 35.6620, "lng": 139.7018, "concept": "Brand Center", "image_url": ""},
    {"store_id": "KR001", "store_name": "adidas Brand Flagship Seoul", "country": "Korea", "city": "Seoul", "address": "Myeongdong 8-gil 27, Jung-gu, Seoul", "lat": 37.5615, "lng": 126.9850, "concept": "Brand Flagship", "image_url": ""}
]

def update_google_sheet():
    df = pd.DataFrame(ALL_STORES)
    
    # 1. 照片公式
    df["photo"] = df["image_url"].apply(
        lambda url: f'=IMAGE("{url}")' if url else ""
    )
    
    # 2. 自動生成 Google 地圖搜尋超連結
    df["map_link"] = df.apply(
        lambda row: f'=HYPERLINK("https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(row["store_name"] + " " + row["address"])}", "📍 開啟地圖")',
        axis=1
    )
    
    # 3. 自動生成 Google 網頁搜尋超連結
    df["web_search"] = df["store_name"].apply(
        lambda name: f'=HYPERLINK("https://www.google.com/search?q={urllib.parse.quote(name)}", "🔍 搜尋網頁")'
    )
    
    # 調整欄位順序與名稱
    cols = ["store_id", "store_name", "photo", "map_link", "web_search", "country", "city", "address", "concept"]
    df = df[cols]
    df["updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

    print(f"🚀 正在寫入包含自動導向連結的門市資料至 Google 試算表...")
    creds_json = os.environ.get("GOOGLE_CREDS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        gc = gspread.service_account(filename="google_creds.json")

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    if spreadsheet_id:
        sh = gc.open_by_key(spreadsheet_id)
    else:
        sh = gc.open_by_key("YOUR_SPREADSHEET_ID")

    worksheet = sh.sheet1
    worksheet.clear()
    
    # 使用 USER_ENTERED 確保 =HYPERLINK() 能轉為可點擊連結
    worksheet.update(
        [df.columns.values.tolist()] + df.values.tolist(),
        value_input_option="USER_ENTERED"
    )
    print("✅ 成功寫入資料！")

if __name__ == "__main__":
    update_google_sheet()
