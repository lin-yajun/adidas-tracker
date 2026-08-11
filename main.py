import os
import json
import urllib.parse
import pandas as pd
import gspread

# 涵蓋台灣全區、日韓重點城市與全球旗艦店的完整門市資料庫
ALL_STORES = [
    # ==================== 台灣門市 ====================
    {"store_id": "TW001", "store_name": "adidas Brand Center 台北品牌概念店", "country": "Taiwan", "city": "台北市", "address": "台北市信義區松壽路18號", "lat": 25.0355, "lng": 121.5672, "concept": "Brand Center", "image_url": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=500"},
    {"store_id": "TW002", "store_name": "adidas 忠孝門市", "country": "Taiwan", "city": "台北市", "address": "台北市大安區忠孝東路四段183號", "lat": 25.0416, "lng": 121.5518, "concept": "Performance Store", "image_url": "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=500"},
    {"store_id": "TW003", "store_name": "adidas Originals 南西門市", "country": "Taiwan", "city": "台北市", "address": "台北市中山區中山北路二段16巷3號", "lat": 25.0531, "lng": 121.5208, "concept": "Originals Store", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"},
    {"store_id": "TW004", "store_name": "adidas 西門町門市", "country": "Taiwan", "city": "台北市", "address": "台北市萬華區峨眉街21號", "lat": 25.0435, "lng": 121.5068, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW005", "store_name": "adidas 信義A11專櫃", "country": "Taiwan", "city": "台北市", "address": "台北市信義區松壽路11號4樓", "lat": 25.0362, "lng": 121.5670, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW006", "store_name": "adidas 京站門市", "country": "Taiwan", "city": "台北市", "address": "台北市大同區承德路一段1號B2", "lat": 25.0492, "lng": 121.5173, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW009", "store_name": "adidas 板橋大遠百門市", "country": "Taiwan", "city": "新北市", "address": "新北市板橋區新站路28號6樓", "lat": 25.0135, "lng": 121.4651, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW010", "store_name": "adidas 三井 Outlet 林口", "country": "Taiwan", "city": "新北市", "address": "新北市林口區文化三路一段356號", "lat": 25.0712, "lng": 121.3662, "concept": "Factory Outlet", "image_url": ""},
    {"store_id": "TW014", "store_name": "adidas 華泰名品城 Outlet", "country": "Taiwan", "city": "桃園市", "address": "桃園市中壢區春德路189號", "lat": 25.0125, "lng": 121.2138, "concept": "Factory Outlet", "image_url": ""},
    {"store_id": "TW017", "store_name": "adidas 新竹巨城門市", "country": "Taiwan", "city": "新竹市", "address": "新竹市東區中央路229號1F", "lat": 24.8097, "lng": 120.9751, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW020", "store_name": "adidas 台中綠園道概念店", "country": "Taiwan", "city": "台中市", "address": "台中市西區公益路68號", "lat": 24.1511, "lng": 120.6638, "concept": "Brand Center", "image_url": ""},
    {"store_id": "TW023", "store_name": "adidas 三井 Outlet 台中港", "country": "Taiwan", "city": "台中市", "address": "台中市梧棲區臺灣大道十段168號", "lat": 24.2562, "lng": 120.5218, "concept": "Factory Outlet", "image_url": ""},
    {"store_id": "TW027", "store_name": "adidas 南紡購物中心門市", "country": "Taiwan", "city": "台南市", "address": "台南市東區中華東路一段366號", "lat": 22.9908, "lng": 120.2335, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW030", "store_name": "adidas 高雄漢神巨蛋門市", "country": "Taiwan", "city": "高雄市", "address": "高雄市左營區博愛二路777號8F", "lat": 22.6695, "lng": 120.3023, "concept": "Performance Store", "image_url": ""},
    {"store_id": "TW031", "store_name": "adidas SKM Park Outlet 高雄草衙", "country": "Taiwan", "city": "高雄市", "address": "高雄市前鎮區中安路1-1號", "lat": 22.5812, "lng": 120.3308, "concept": "Factory Outlet", "image_url": ""},

    # ==================== 日本門市 (Japan) ====================
    # --- 東京首都圈 ---
    {"store_id": "JP001", "store_name": "adidas Brand Center RAYARD MIYASHITA PARK", "country": "Japan", "city": "Tokyo", "address": "6-20-10 Jingumae, Shibuya-ku, Tokyo", "lat": 35.6620, "lng": 139.7018, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP002", "store_name": "adidas Originals Flagship Store Tokyo (原宿)", "country": "Japan", "city": "Tokyo", "address": "5-17-4 Jingumae, Shibuya-ku, Tokyo", "lat": 35.6662, "lng": 139.7065, "concept": "Originals Store", "image_url": ""},
    {"store_id": "JP003", "store_name": "adidas Brand Center Ginza (銀座)", "country": "Japan", "city": "Tokyo", "address": "2-2-14 Ginza, Chuo-ku, Tokyo", "lat": 35.6738, "lng": 139.7645, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP004", "store_name": "adidas Brand Center Shinjuku (新宿)", "country": "Japan", "city": "Tokyo", "address": "3-27-4 Shinjuku, Shinjuku-ku, Tokyo", "lat": 35.6905, "lng": 139.7020, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP005", "store_name": "adidas Brand Center Ikebukuro (池袋)", "country": "Japan", "city": "Tokyo", "address": "1-50-3 Higashi-Ikebukuro, Toshima-ku, Tokyo", "lat": 35.7289, "lng": 139.7125, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP006", "store_name": "adidas Factory Outlet 酒井 (Shisui Outlet)", "country": "Japan", "city": "Chiba", "address": "2-4-1 Iizumi, Shisui-machi, Inba-gun, Chiba", "lat": 35.7312, "lng": 140.2851, "concept": "Factory Outlet", "image_url": ""},
    
    # --- 關西地區 (大阪/京都) ---
    {"store_id": "JP007", "store_name": "adidas Brand Center Shinsaibashi (心齋橋)", "country": "Japan", "city": "Osaka", "address": "1-15-14 Shinsaibashisuji, Chuo-ku, Osaka", "lat": 34.6718, "lng": 135.5012, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP008", "store_name": "adidas Originals Shop Umeda (梅田)", "country": "Japan", "city": "Osaka", "address": "HEP FIVE 5F, 5-15 Kakudacho, Kita-ku, Osaka", "lat": 34.7035, "lng": 135.4998, "concept": "Originals Store", "image_url": ""},
    {"store_id": "JP009", "store_name": "adidas Brand Center Kyoto (京都)", "country": "Japan", "city": "Kyoto", "address": "58 Tachiuri Nakanocho, Shimogyo-ku, Kyoto", "lat": 35.0038, "lng": 135.7648, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP010", "store_name": "adidas Factory Outlet 臨空城 (Rinku Outlet)", "country": "Japan", "city": "Osaka", "address": "3-28 Rinku Ouraiminami, Izumisano, Osaka", "lat": 34.4068, "lng": 135.2952, "concept": "Factory Outlet", "image_url": ""},

    # --- 福岡 / 北海道 / 沖繩 ---
    {"store_id": "JP011", "store_name": "adidas Brand Center Fukuoka (福岡天神)", "country": "Japan", "city": "Fukuoka", "address": "2-2-43 Tenjin, Chuo-ku, Fukuoka", "lat": 33.5885, "lng": 130.3982, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP012", "store_name": "adidas Brand Center Sapporo (札幌)", "country": "Japan", "city": "Hokkaido", "address": "Minami 3-jo Nishi 2-chome, Chuo-ku, Sapporo", "lat": 43.0578, "lng": 141.3542, "concept": "Brand Center", "image_url": ""},
    {"store_id": "JP013", "store_name": "adidas Factory Outlet 沖繩 ASHIBINAA", "country": "Japan", "city": "Okinawa", "address": "1-188 Toyosaki, Tomigusuku, Okinawa", "lat": 26.1578, "lng": 127.6538, "concept": "Factory Outlet", "image_url": ""},

    # ==================== 韓國門市 (Korea) ====================
    # --- 首爾圈 ---
    {"store_id": "KR001", "store_name": "adidas Brand Flagship Seoul (明洞旗艦店)", "country": "Korea", "city": "Seoul", "address": "Myeongdong 8-gil 27, Jung-gu, Seoul", "lat": 37.5615, "lng": 126.9850, "concept": "Brand Flagship", "image_url": ""},
    {"store_id": "KR002", "store_name": "adidas Originals Shop Hongdae (弘大專賣店)", "country": "Korea", "city": "Seoul", "address": "Hongik-ro 6-gil 27, Mapo-gu, Seoul", "lat": 37.5552, "lng": 126.9231, "concept": "Originals Store", "image_url": ""},
    {"store_id": "KR003", "store_name": "adidas Gangnam Brand Center (江南品牌中心)", "country": "Korea", "city": "Seoul", "address": "481 Gangnam-daero, Seocho-gu, Seoul", "lat": 37.5048, "lng": 127.0252, "concept": "Brand Center", "image_url": ""},
    {"store_id": "KR004", "store_name": "adidas Originals Shop Seongsu (聖水洞概念店)", "country": "Korea", "city": "Seoul", "address": "13 Yeonmujang 7-gil, Seongdong-gu, Seoul", "lat": 37.5438, "lng": 127.0568, "concept": "Originals Store", "image_url": ""},
    {"store_id": "KR005", "store_name": "adidas Originals Shop Garosugil (新沙洞林蔭道)", "country": "Korea", "city": "Seoul", "address": "528-5 Sinsa-dong, Gangnam-gu, Seoul", "lat": 37.5208, "lng": 127.0228, "concept": "Originals Store", "image_url": ""},
    {"store_id": "KR006", "store_name": "adidas Outlet 坡州名牌折扣購物中心 (Paju Outlet)", "country": "Korea", "city": "Gyeonggi-do", "address": "200 Pilseung-ro, Tanhyeon-myeon, Paju-si", "lat": 37.7692, "lng": 126.6985, "concept": "Factory Outlet", "image_url": ""},

    # --- 釜山 / 濟州島 ---
    {"store_id": "KR007", "store_name": "adidas Brand Center Busan Seomyun (釜山西面)", "country": "Korea", "city": "Busan", "address": "692 Central-daero, Busanjin-gu, Busan", "lat": 35.1558, "lng": 129.0592, "concept": "Brand Center", "image_url": ""},
    {"store_id": "KR008", "store_name": "adidas Originals Shop Gwangbok (釜山光復洞)", "country": "Korea", "city": "Busan", "address": "56 Gwangbok-ro, Jung-gu, Busan", "lat": 35.0988, "lng": 129.0315, "concept": "Originals Store", "image_url": ""},
    {"store_id": "KR009", "store_name": "adidas Store Jeju (濟州七星路店)", "country": "Korea", "city": "Jeju", "address": "21 Chilseong-ro, Jeju-si, Jeju-do", "lat": 33.5135, "lng": 126.5268, "concept": "Performance Store", "image_url": ""},

    # ==================== 歐美重點旗艦店 ====================
    {"store_id": "US001", "store_name": "adidas Fifth Avenue Flagship", "country": "United States", "city": "New York", "address": "565 5th Ave, New York, NY 10017", "lat": 40.7562, "lng": -73.9789, "concept": "Flagship Store", "image_url": ""},
    {"store_id": "UK001", "store_name": "adidas Oxford Street Flagship", "country": "United Kingdom", "city": "London", "address": "425 Oxford St, London W1D 2PS", "lat": 51.5145, "lng": -0.1512, "concept": "Flagship Store", "image_url": ""}
]

def update_google_sheet():
    df = pd.DataFrame(ALL_STORES)
    
    # 1. 圖片公式
    df["photo"] = df["image_url"].apply(
        lambda url: f'=IMAGE("{url}")' if url else ""
    )
    
    # 2. 地圖導航超連結
    df["map_link"] = df.apply(
        lambda row: f'=HYPERLINK("https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(row["store_name"] + " " + row["address"])}", "📍 開啟地圖")',
        axis=1
    )
    
    # 3. 網頁搜尋超連結
    df["web_search"] = df["store_name"].apply(
        lambda name: f'=HYPERLINK("https://www.google.com/search?q={urllib.parse.quote(name)}", "🔍 搜尋網頁")'
    )
    
    # 欄位排序
    cols = ["store_id", "store_name", "photo", "map_link", "web_search", "country", "city", "address", "concept", "lat", "lng", "image_url"]
    df = df[cols]
    df["updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

    print(f"🚀 正在寫入 {len(df)} 筆門市資料至 Google 試算表...")
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
    
    worksheet.update(
        [df.columns.values.tolist()] + df.values.tolist(),
        value_input_option="USER_ENTERED"
    )
    print("✅ 成功寫入資料！")

if __name__ == "__main__":
    update_google_sheet()
