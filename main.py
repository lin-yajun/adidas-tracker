import os
import json
import pandas as pd
import gspread

# 擴充版門市資料庫 (涵蓋台灣各區與全球主要重點門市)
ALL_STORES = [
    # --- 台灣：台北 / 新北 ---
    {"store_id": "TW001", "store_name": "adidas Brand Center 台北品牌概念店", "country": "Taiwan", "city": "台北市", "address": "台北市信義區松壽路18號", "lat": 25.0355, "lng": 121.5672, "concept": "Brand Center"},
    {"store_id": "TW002", "store_name": "adidas 忠孝門市", "country": "Taiwan", "city": "台北市", "address": "台北市大安區忠孝東路四段183號", "lat": 25.0416, "lng": 121.5518, "concept": "Performance Store"},
    {"store_id": "TW003", "store_name": "adidas Originals 南西門市", "country": "Taiwan", "city": "台北市", "address": "台北市中山區中山北路二段16巷3號", "lat": 25.0531, "lng": 121.5208, "concept": "Originals Store"},
    {"store_id": "TW004", "store_name": "adidas 西門町門市", "country": "Taiwan", "city": "台北市", "address": "台北市萬華區峨眉街21號", "lat": 25.0435, "lng": 121.5068, "concept": "Performance Store"},
    {"store_id": "TW005", "store_name": "adidas 信義A11專櫃", "country": "Taiwan", "city": "台北市", "address": "台北市信義區松壽路11號4樓", "lat": 25.0362, "lng": 121.5670, "concept": "Performance Store"},
    {"store_id": "TW006", "store_name": "adidas 京站門市", "country": "Taiwan", "city": "台北市", "address": "台北市大同區承德路一段1號B2", "lat": 25.0492, "lng": 121.5173, "concept": "Performance Store"},
    {"store_id": "TW007", "store_name": "adidas 板橋大遠百門市", "country": "Taiwan", "city": "新北市", "address": "新北市板橋區新站路28號6樓", "lat": 25.0135, "lng": 121.4651, "concept": "Performance Store"},
    {"store_id": "TW008", "store_name": "adidas 三井 Outlet 林口", "country": "Taiwan", "city": "新北市", "address": "新北市林口區文化三路一段356號", "lat": 25.0712, "lng": 121.3662, "concept": "Factory Outlet"},

    # --- 台灣：桃竹苗 ---
    {"store_id": "TW009", "store_name": "adidas 華泰名品城 Outlet", "country": "Taiwan", "city": "桃園市", "address": "桃園市中壢區春德路189號", "lat": 25.0125, "lng": 121.2138, "concept": "Factory Outlet"},
    {"store_id": "TW010", "store_name": "adidas 桃園台茂門市", "country": "Taiwan", "city": "桃園市", "address": "桃園市蘆竹區南崁路一段112號", "lat": 25.0538, "lng": 121.2881, "concept": "Performance Store"},
    {"store_id": "TW011", "store_name": "adidas 新竹巨城門市", "country": "Taiwan", "city": "新竹市", "address": "新竹市東區中央路229號1F", "lat": 24.8097, "lng": 120.9751, "concept": "Performance Store"},

    # --- 台灣：台中 / 彰化 ---
    {"store_id": "TW012", "store_name": "adidas 台中綠園道概念店", "country": "Taiwan", "city": "台中市", "address": "台中市西區公益路68號", "lat": 24.1511, "lng": 120.6638, "concept": "Brand Center"},
    {"store_id": "TW013", "store_name": "adidas 台中大遠百門市", "country": "Taiwan", "city": "台中市", "address": "台中市西屯區台灣大道三段251號7樓", "lat": 24.1658, "lng": 120.6415, "concept": "Performance Store"},
    {"store_id": "TW014", "store_name": "adidas 三井 Outlet 台中港", "country": "Taiwan", "city": "台中市", "address": "台中市梧棲區臺灣大道十段168號", "lat": 24.2562, "lng": 120.5218, "concept": "Factory Outlet"},
    {"store_id": "TW015", "store_name": "adidas 麗寶 Outlet Mall", "country": "Taiwan", "city": "台中市", "address": "台中市后里區福容路201號", "lat": 24.3235, "lng": 120.7028, "concept": "Factory Outlet"},

    # --- 台灣：台南 / 高雄 ---
    {"store_id": "TW016", "store_name": "adidas 南紡購物中心門市", "country": "Taiwan", "city": "台南市", "address": "台南市東區中華東路一段366號", "lat": 22.9908, "lng": 120.2335, "concept": "Performance Store"},
    {"store_id": "TW017", "store_name": "adidas 三井 Outlet 台南", "country": "Taiwan", "city": "台南市", "address": "台南市歸仁區歸仁大道101號", "lat": 22.9238, "lng": 120.2858, "concept": "Factory Outlet"},
    {"store_id": "TW018", "store_name": "adidas 高雄漢神巨蛋門市", "country": "Taiwan", "city": "高雄市", "address": "高雄市左營區博愛二路777號8F", "lat": 22.6695, "lng": 120.3023, "concept": "Performance Store"},
    {"store_id": "TW019", "store_name": "adidas SKM Park Outlet 高雄草衙", "country": "Taiwan", "city": "高雄市", "address": "高雄市前鎮區中安路1-1號", "lat": 22.5812, "lng": 120.3308, "concept": "Factory Outlet"},

    # --- 海外：日本 / 韓國 / 美國 / 歐洲 ---
    {"store_id": "JP001", "store_name": "adidas Brand Center RAYARD MIYASHITA PARK", "country": "Japan", "city": "Tokyo", "address": "6-20-10 Jingumae, Shibuya-ku, Tokyo", "lat": 35.6620, "lng": 139.7018, "concept": "Brand Center"},
    {"store_id": "JP002", "store_name": "adidas Originals Flagship Store Tokyo", "country": "Japan", "city": "Tokyo", "address": "5-17-4 Jingumae, Shibuya-ku, Tokyo", "lat": 35.6662, "lng": 139.7065, "concept": "Originals Store"},
    {"store_id": "JP003", "store_name": "adidas Brand Center Ginza", "country": "Japan", "city": "Tokyo", "address": "2-2-14 Ginza, Chuo-ku, Tokyo", "lat": 35.6738, "lng": 139.7645, "concept": "Brand Center"},
    {"store_id": "KR001", "store_name": "adidas Brand Flagship Seoul", "country": "Korea", "city": "Seoul", "address": "Myeongdong 8-gil 27, Jung-gu, Seoul", "lat": 37.5615, "lng": 126.9850, "concept": "Brand Flagship"},
    {"store_id": "KR002", "store_name": "adidas Originals Store Hongdae", "country": "Korea", "city": "Seoul", "address": "Hongik-ro 6-gil 27, Mapo-gu, Seoul", "lat": 37.5552, "lng": 126.9231, "concept": "Originals Store"},
    {"store_id": "US001", "store_name": "adidas Fifth Avenue Flagship", "country": "United States", "city": "New York", "address": "565 5th Ave, New York, NY 10017", "lat": 40.7562, "lng": -73.9789, "concept": "Flagship Store"},
    {"store_id": "US002", "store_name": "adidas Store Los Angeles Downtown", "country": "United States", "city": "Los Angeles", "address": "800 S Broadway, Los Angeles, CA 90014", "lat": 34.0438, "lng": -118.2541, "concept": "Performance Store"},
    {"store_id": "UK001", "store_name": "adidas Oxford Street Flagship", "country": "United Kingdom", "city": "London", "address": "425 Oxford St, London W1D 2PS", "lat": 51.5145, "lng": -0.1512, "concept": "Flagship Store"}
]

def update_google_sheet():
    df = pd.DataFrame(ALL_STORES)
    df["updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"🚀 準備寫入 {len(df)} 筆門市資料至 Google 試算表...")
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
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"✅ 成功寫入 {len(df)} 筆資料至 Google 試算表！")

if __name__ == "__main__":
    update_google_sheet()
