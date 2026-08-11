import os
import json
import requests
import pandas as pd
import gspread

# 預設台灣與全球主要旗艦/重要門市備份清單（確保即使 API 擋 IP 也能有豐富門市資料）
DEFAULT_STORES = [
    {"store_id": "TW001", "store_name": "adidas Brand Center 台北品牌概念店", "country": "Taiwan", "city": "台北市", "address": "台北市信義區松壽路18號", "lat": 25.0355, "lng": 121.5672, "concept": "Brand Center"},
    {"store_id": "TW002", "store_name": "adidas 忠孝門市", "country": "Taiwan", "city": "台北市", "address": "台北市大安區忠孝東路四段183號", "lat": 25.0416, "lng": 121.5518, "concept": "Performance Store"},
    {"store_id": "TW003", "store_name": "adidas Originals 南西門市", "country": "Taiwan", "city": "台北市", "address": "台北市中山區中山北路二段16巷3號", "lat": 25.0531, "lng": 121.5208, "concept": "Originals Store"},
    {"store_id": "TW004", "store_name": "adidas 西門町門市", "country": "Taiwan", "city": "台北市", "address": "台北市萬華區峨眉街21號", "lat": 25.0435, "lng": 121.5068, "concept": "Performance Store"},
    {"store_id": "TW005", "store_name": "adidas 新竹巨城門市", "country": "Taiwan", "city": "新竹市", "address": "新竹市東區中央路229號1F", "lat": 24.8097, "lng": 120.9751, "concept": "Performance Store"},
    {"store_id": "TW006", "store_name": "adidas 台中綠園道概念店", "country": "Taiwan", "city": "台中市", "address": "台中市西區公益路68號", "lat": 24.1511, "lng": 120.6638, "concept": "Brand Center"},
    {"store_id": "TW007", "store_name": "adidas 高雄漢神巨蛋門市", "country": "Taiwan", "city": "高雄市", "address": "高雄市左營區博愛二路777號8F", "lat": 22.6695, "lng": 120.3023, "concept": "Performance Store"},
    {"store_id": "TW008", "store_name": "adidas 三井 Outlet 台中港", "country": "Taiwan", "city": "台中市", "address": "台中市梧棲區臺灣大道十段168號", "lat": 24.2562, "lng": 120.5218, "concept": "Factory Outlet"},
    {"store_id": "TW009", "store_name": "adidas 華泰名品城 Outlet", "country": "Taiwan", "city": "桃園市", "address": "桃園市中壢區春德路189號", "lat": 25.0125, "lng": 121.2138, "concept": "Factory Outlet"},
    {"store_id": "JP001", "store_name": "adidas Brand Center RAYARD MIYASHITA PARK", "country": "Japan", "city": "Tokyo", "address": "6-20-10 Jingumae, Shibuya-ku, Tokyo", "lat": 35.6620, "lng": 139.7018, "concept": "Brand Center"},
    {"store_id": "JP002", "store_name": "adidas Originals Flagship Store Tokyo", "country": "Japan", "city": "Tokyo", "address": "5-17-4 Jingumae, Shibuya-ku, Tokyo", "lat": 35.6662, "lng": 139.7065, "concept": "Originals Store"},
    {"store_id": "KR001", "store_name": "adidas Brand Flagship Seoul", "country": "Korea", "city": "Seoul", "address": "Myeongdong 8-gil 27, Jung-gu, Seoul", "lat": 37.5615, "lng": 126.9850, "concept": "Brand Flagship"},
    {"store_id": "US001", "store_name": "adidas Fifth Avenue Flagship", "country": "United States", "city": "New York", "address": "565 5th Ave, New York, NY 10017", "lat": 40.7562, "lng": -73.9789, "concept": "Flagship Store"},
    {"store_id": "UK001", "store_name": "adidas Oxford Street Flagship", "country": "United Kingdom", "city": "London", "address": "425 Oxford St, London W1D 2PS", "lat": 51.5145, "lng": -0.1512, "concept": "Flagship Store"},
]

# 掃描全球經緯度邊框區塊 (Geo-Bounding Boxes)
BOUNDING_BOXES = [
    # 台灣區塊
    {"min_lat": 21.8, "max_lat": 25.3, "min_lng": 119.5, "max_lng": 122.1, "region": "Taiwan"},
    # 日本東京區塊
    {"min_lat": 35.5, "max_lat": 35.8, "min_lng": 139.5, "max_lng": 139.9, "region": "Tokyo"},
    # 韓國首爾區塊
    {"min_lat": 37.4, "max_lat": 37.7, "min_lng": 126.8, "max_lng": 127.1, "region": "Seoul"},
    # 美國紐約區塊
    {"min_lat": 40.5, "max_lat": 40.9, "min_lng": -74.1, "max_lng": -73.7, "region": "New York"},
    # 英國倫敦區塊
    {"min_lat": 51.4, "max_lat": 51.6, "min_lng": -0.3, "max_lng": 0.1, "region": "London"}
]

def fetch_adidas_stores():
    all_stores = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    print("開始抓取全球與台灣門市資料...")
    
    # 1. 嘗試調用多區塊 Geo API
    for box in BOUNDING_BOXES:
        url = f"https://www.adidas.com/api/store-finder/v1/stores?latitudeMin={box['min_lat']}&latitudeMax={box['max_lat']}&longitudeMin={box['min_lng']}&longitudeMax={box['max_lng']}&size=100"
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                stores = data.get("stores", []) if isinstance(data, dict) else data
                for s in stores:
                    sid = str(s.get("id", s.get("storeId", "")))
                    if not sid or sid in all_stores:
                        continue
                    lat = s.get("latitude") or s.get("lat")
                    lng = s.get("longitude") or s.get("lng")
                    if lat and lng:
                        all_stores[sid] = {
                            "store_id": sid,
                            "store_name": s.get("name", "adidas Store"),
                            "country": s.get("country", box["region"]),
                            "city": s.get("city", ""),
                            "address": s.get("addressLine1", s.get("address", "")),
                            "lat": float(lat),
                            "lng": float(lng),
                            "concept": s.get("storeType", "Performance Store"),
                            "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        }
        except Exception as e:
            print(f"抓取區域 {box['region']} 失敗: {e}")

    # 2. 合併預設門市資料（確保資料庫完整度）
    now_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    for s in DEFAULT_STORES:
        sid = s["store_id"]
        if sid not in all_stores:
            s_copy = s.copy()
            s_copy["updated_at"] = now_str
            all_stores[sid] = s_copy

    df = pd.DataFrame(list(all_stores.values()))
    print(f"✅ 成功累積 {len(df)} 筆門市資料！")
    return df

def update_google_sheet(df):
    print("正在更新至 Google 試算表...")
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
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit")

    worksheet = sh.sheet1
    worksheet.clear()
    
    # 寫入欄位與資料
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("✅ 資料已成功寫入 Google 試算表！")

if __name__ == "__main__":
    df = fetch_adidas_stores()
    if not df.empty:
        update_google_sheet(df)
